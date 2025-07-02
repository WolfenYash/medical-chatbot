import os
# from langchain_openai import OpenAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from flask import Flask, flash, url_for, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine, text

# from langchain_community.vectorstores import Chroma {outdated}
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("No API key found")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

engine = create_engine("sqlite:///example.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    if "user" in session:
        return render_template("index.html")
    else:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        print("here in login", flush=True)
        username = request.form.get("username")
        password = request.form.get("password")
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT * FROM users WHERE username = :username AND password = :password"),
                {"username": username, "password": password}
            ).fetchone()
            if result:
                session["user"] = username
                flash("Login successful!", "success")
                return redirect(url_for("index"))
            else:
                flash("Invalid username or password", "danger")
                return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("register"))
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT * FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()
            if result:
                flash("Username already exists", "danger")
                return redirect(url_for("register"))
            conn.execute(
                text("INSERT INTO users (username, password) VALUES (:username, :password)"),
                {"username": username, "password": password}
            )
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if "user" not in session:
        flash("Please log in to access the chatbot.", "danger")
        return redirect(url_for("login"))

    with engine.begin() as conn:
        profile = conn.execute(
            text("SELECT * FROM profiles WHERE username = :username"),
            {"username": session["user"]}
        ).fetchone()

    if not profile:
        flash("Please complete your profile first.", "warning")
        return redirect(url_for("save_profile"))

    profile_str = f"""
    Age: {profile.age}
    Gender: {profile.gender}
    Height: {profile.height_cm} cm
    Weight: {profile.weight_kg} kg
    Medical Conditions: {profile.conditions}
    Medications: {profile.medications}
    Allergies: {profile.allergies}
    Surgeries: {profile.surgeries}
    Diet: {profile.diet}
    Exercise Frequency: {profile.exercise}
    Smokes: {profile.smoking}
    Alcohol Consumption: {profile.alcohol}
    Sleep per Night: {profile.sleep_hours} hours
    Family History: {profile.family_history}
    """

    if request.method == "POST":
        user_input = request.form.get("user_input")
        if not user_input:
            flash("Please enter a question.", "warning")
            return render_template("chat.html", response=None)
        # classifier_prompt = PromptTemplate(
        # input_variables=["question"],
        # template="You are a strict medical classifier. Reply ONLY 'yes' or 'no'. Consider a question healthcare-related if it involves symptoms, diseases, treatments, or anything about the user's health profile, lifestyle, diet, sleep, or physical condition.\nQuestion: {question}"

        # )

        # classifier_llm = OpenAI(temperature=0)
        # result = classifier_llm.invoke(classifier_prompt.format(question=user_input))

        # if "no" in result.lower():
        #     return render_template("chat.html", response="Sorry, I can only answer healthcare-related questions.")

        # Step 1: Retrieve documents from Chroma
        embedding = OpenAIEmbeddings()
        db = Chroma(persist_directory="chroma_db", embedding_function=embedding)
        docs = db.similarity_search(user_input, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])

        # Step 2: Build a structured prompt using PromptTemplate
        rag_prompt = PromptTemplate(
            input_variables=["profile", "context", "question"],
            template=(
                "You are a helpful and medically accurate assistant.\n"
                "Use the following user profile and medical documents to answer the question.\n\n"
                "User Profile:\n{profile}\n\n"
                "Medical Context:\n{context}\n\n"
                "Question: {question}\n\n"
                "Answer:"
            )
        )

        # Step 3: Format the final prompt
        final_prompt = rag_prompt.format(
            profile=profile_str,
            context=context,
            question=user_input
        )



        # Step 4: Call the language model to generate a response
        llm = ChatOpenAI(temperature=0.3)
        response = llm.invoke(final_prompt)
        response = response.content
        with engine.begin() as conn:
            # Save the user input to the chat history
            conn.execute(
                text("INSERT INTO chat_history (username, user_message, bot_response) VALUES (:username, :message, :bot_response)"),
                {"username": session["user"], "message": user_input, "bot_response": response}
            )
        sources = []
        seen = set()
        for doc in docs:
            filename = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", None)
            label = f"{filename} (page {page + 1})" if page is not None else filename
            if label not in seen:
                sources.append(label)
                seen.add(label)

        return render_template("chat.html", response= response,sources = sources)
    return render_template("chat.html", response=None)

@app.route("/profile", methods=["GET", "POST"])
def save_profile():
    if "user" not in session:
        flash("You must be logged in to access this page", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        data = {
            "username": session["user"],
            "age": request.form.get("age"),
            "gender": request.form.get("gender"),
            "height": request.form.get("height"),
            "weight": request.form.get("weight"),
            "conditions": request.form.get("conditions"),
            "medications": request.form.get("medications"),
            "allergies": request.form.get("allergies"),
            "surgeries": request.form.get("surgeries"),
            "diet": request.form.get("diet"),
            "exercise": request.form.get("exercise"),
            "smoking": request.form.get("smoking"),
            "alcohol": request.form.get("alcohol"),
            "sleep_hours": request.form.get("sleep_hours"),
            "family_history": request.form.get("family_history")
        }

        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT * FROM profiles WHERE username = :username"),
                {"username": data["username"]}
            ).fetchone()

            if result:
                conn.execute(text("""
                    UPDATE profiles SET
                        age = :age, gender = :gender, height_cm = :height,
                        weight_kg = :weight, conditions = :conditions, medications = :medications,
                        allergies = :allergies, surgeries = :surgeries, diet = :diet,
                        exercise = :exercise, smoking = :smoking, alcohol = :alcohol,
                        sleep_hours = :sleep_hours, family_history = :family_history
                    WHERE username = :username
                """), data)
            else:
                conn.execute(text("""
                    INSERT INTO profiles (
                        username, age, gender, height_cm, weight_kg, conditions,
                        medications, allergies, surgeries, diet, exercise,
                        smoking, alcohol, sleep_hours, family_history
                    ) VALUES (
                        :username, :age, :gender, :height, :weight, :conditions,
                        :medications, :allergies, :surgeries, :diet, :exercise,
                        :smoking, :alcohol, :sleep_hours, :family_history
                    )
                """), data)

        flash("Profile saved successfully!", "success")
        return redirect(url_for("chatbot"))

    return render_template("personalize.html")
@app.route("/history",methods=["GET", "POST"])
def history():
    if "user" not in session:
        flash("You must be logged in to access this page", "danger")
        return redirect(url_for("login"))

    with engine.begin() as conn:
        chats = conn.execute(
            text("SELECT * FROM chat_history WHERE username = :username ORDER BY timestamp DESC"),
            {"username": session["user"]}
        ).fetchall()

    return render_template("history.html", chats=chats)

if __name__ == "__main__":
    app.run(debug=True)

# host = "127.0.0.1", port = 5001,