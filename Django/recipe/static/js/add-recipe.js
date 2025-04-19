const nav = document.querySelector('.nav');
if (nav) {
    let timeoutID;
    
    function hideNav() {
        timeoutID = setTimeout(() => {
            nav.classList.add('hidden');
        }, 3000);
        }
    function showNav() {
        clearTimeout(timeoutID);
        nav.classList.remove('hidden');
    }
    document.addEventListener('mousemove', showNav);
    hideNav();
} else {
    console.error('.nav element not found');
}

