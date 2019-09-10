let tvpTab = document.getElementById('tvp-tab');
let uncTab = document.getElementById('unc-tab');
let tabs = [tvpTab, uncTab];
let plotElements = {'tvp-tab': document.getElementById('true_vs_predicted'),
                    'unc-tab': document.getElementById('uncertainty_validation')}

function changeTab(e) {
    // Add active only to selected tab
    tabs.forEach(tab => {
        tab.classList.remove('active');
        plotElements[tab.id].classList.remove('active');
    })
    e.target.classList.add('active');
    plotElements[e.target.id].classList.add('active');
}

tvpTab.onclick = changeTab;
uncTab.onclick = changeTab;