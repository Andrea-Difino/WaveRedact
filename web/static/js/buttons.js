const securityButtons = document.querySelectorAll(".security-tabs button");

const slider = document.querySelector(".security-tabs .slider");

const lists = document.querySelectorAll(".preset-list");

securityButtons.forEach((btn, index) => {

    btn.addEventListener("click", () => {

        securityButtons.forEach(b =>
            b.classList.remove("active")
        );

        btn.classList.add("active");

        slider.style.transform =
            `translateX(${index * 100}%)`;

        lists.forEach(l =>
            l.classList.remove("active")
        );

        document
            .getElementById(
                btn.dataset.level + "-list"
            )
            .classList.add("active");

    });

});

const modeButtons = document.querySelectorAll(".mode-tabs button");
const modeSlider = document.querySelector(".mode-tabs .slider");

modeButtons.forEach((btn, index) => {

    btn.addEventListener("click", () => {

        modeButtons.forEach(b =>
            b.classList.remove("active")
        );

        btn.classList.add("active");

        modeSlider.style.transform =
            `translateX(${index * 100}%)`;

    });

});

const buttons = document.querySelectorAll('.segmented button');
const securityInfo = document.querySelector('.security-info');

let revealed = false;

buttons.forEach(btn => {
    btn.addEventListener('click', () => {

        if (!revealed) {
            securityInfo.classList.add('visible');
            revealed = true;
        }

    });
});