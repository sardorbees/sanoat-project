document.addEventListener('DOMContentLoaded', function () {
    const logo = document.querySelector('.animated-logo');
    if (logo) {
        logo.style.opacity = 0;
        setTimeout(() => {
            logo.style.transition = 'opacity 1s ease-in-out';
            logo.style.opacity = 1;
        }, 500);
    }
});
