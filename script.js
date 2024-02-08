document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector('form');
    const loadingScreen = document.getElementById("loading-screen");
    const content = document.querySelector('.container');
    const spinner = document.querySelector('.spinner');

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        // Show loading screen and spinner
        showLoadingScreen();

        // Simulate an asynchronous data loading process
        setTimeout(function () {
            // After loading is complete, hide the loading screen and spinner
            hideLoadingScreen();
        }, 2000); // Adjust the timeout as needed (in milliseconds)
    });

    function showLoadingScreen() {
        loadingScreen.style.display = "flex";
        content.style.display = "none";
        spinner.style.display = "block";
    }

    function hideLoadingScreen() {
        loadingScreen.style.display = "none";
        content.style.display = "block";
        spinner.style.display = "none";
    }
});
