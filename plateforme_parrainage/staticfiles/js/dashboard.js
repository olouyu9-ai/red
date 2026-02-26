document.addEventListener('DOMContentLoaded', () => {
    const soldeSpan = document.querySelector('.solde span');
    if(soldeSpan) {
        const solde = parseInt(soldeSpan.textContent.replace(/\s|FC/g, ''));
        let current = 0;
        const step = Math.ceil(solde / 100);
        const interval = setInterval(() => {
            current += step;
            if(current >= solde) {
                current = solde;
                clearInterval(interval);
            }
            soldeSpan.textContent = current.toLocaleString() + " FC";
        }, 20);
    }
});


// Petit effet JS : animation sur clic bouton
document.querySelectorAll(".bouton").forEach(btn => {
    btn.addEventListener("click", () => {
        btn.style.transform = "scale(0.95)";
        setTimeout(() => btn.style.transform = "scale(1)", 150);
    });
});
