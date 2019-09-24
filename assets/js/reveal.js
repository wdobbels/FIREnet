let banners = document.getElementsByClassName('image-banner');

function setOpaque(banner) {
    // banner.style.opacity = 1;
    banner.classList.remove("hidden");
}

let delay = 300;
Array.from(banners).forEach(banner => {
    window.setTimeout(setOpaque, delay, banner);
    delay += 600;
});

