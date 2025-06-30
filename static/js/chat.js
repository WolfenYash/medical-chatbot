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
