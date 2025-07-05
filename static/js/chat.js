let toggle_sources = document.querySelector('.toggle_button');
let sources = document.querySelector('.sources');
let display = false;
toggle_sources.innerHTML = "Sources ▼";
toggle_sources.addEventListener("click",() =>
    {
        if (display === false)
            {
                toggle_sources.innerHTML = "Sources ▲";
                sources.style.display = "block";
                display = true;
            }
        else
        {
            toggle_sources.innerHTML = "Sources ▼";
            sources.style.display = "none";
            display = false;
        }

    }
);
let button = document.querySelector(".show-btn");
button.addEventListener("click", function () {
    let chat_flow = document.querySelector("#chat-flow");
    chat_flow.classList.toggle("flow");
});