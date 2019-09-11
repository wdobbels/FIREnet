let tvpTab = document.getElementById('tvp-tab');
let uncTab = document.getElementById('unc-tab');
let tabs = [tvpTab, uncTab];
let plotElements = {'tvp-tab': document.getElementById('true_vs_predicted'),
                    'unc-tab': document.getElementById('uncertainty_validation')}

function changeTab(e) {
    let newTab = e.currentTarget;
    // Add active only to selected tab
    tabs.forEach(tab => {
        tab.classList.remove('c-active');
        plotElements[tab.id].classList.remove('c-active');
    })
    newTab.classList.add('c-active');
    plotElements[newTab.id].classList.add('c-active');
}

tvpTab.onclick = changeTab;
// tvpTab.addEventListener('click', changeTab, false);
uncTab.onclick = changeTab;