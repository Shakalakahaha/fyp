// index.js - Main landing page script

document.addEventListener('DOMContentLoaded', function() {
    // Navbar dropdown for mobile
    const dropdownToggle = document.querySelector('.dropdown-toggle');
    
    if (window.innerWidth <= 768) {
        dropdownToggle.addEventListener('click', function(e) {
            e.preventDefault();
            const dropdownMenu = this.nextElementSibling;
            dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
        });
    }
    
    // Enhanced dropdown interactions
    const dropdownItems = document.querySelectorAll('.dropdown-item');
    
    dropdownItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            const icon = item.querySelector('i');
            if (icon) {
                icon.classList.add('animate-pulse');
            }
        });
        
        item.addEventListener('mouseleave', () => {
            const icon = item.querySelector('i');
            if (icon) {
                icon.classList.remove('animate-pulse');
            }
        });
    });
});

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add hover animation effect to the hero image
    const heroImage = document.querySelector('.hero-image');
    if (heroImage) {
        document.addEventListener('mousemove', (e) => {
            const x = e.clientX / window.innerWidth;
            const y = e.clientY / window.innerHeight;
            
            // Calculate subtle rotation based on mouse position
            const rotateX = (y - 0.5) * 5; // -2.5 to 2.5 degrees
            const rotateY = (x - 0.5) * -5; // -2.5 to 2.5 degrees
            
            // Apply transform to the hero image
            heroImage.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(0)`;
        });
        
        // Reset transform when mouse leaves
        document.addEventListener('mouseleave', () => {
            heroImage.style.transform = 'translateY(0)';
        });
    }
    
    // Add a subtle animation to the CTA button
    const ctaButton = document.querySelector('.btn-primary');
    if (ctaButton) {
        ctaButton.addEventListener('mouseenter', () => {
            ctaButton.style.transform = 'translateY(-5px) scale(1.05)';
            ctaButton.style.boxShadow = '0 10px 25px rgba(58, 134, 255, 0.4)';
        });
        
        ctaButton.addEventListener('mouseleave', () => {
            ctaButton.style.transform = 'translateY(-2px) scale(1)';
            ctaButton.style.boxShadow = '0 5px 15px rgba(58, 134, 255, 0.3)';
        });
    }
    
    // Add CSS animation class
    document.head.insertAdjacentHTML('beforeend', `
        <style>
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            .animate-pulse {
                animation: pulse 0.6s ease-in-out infinite;
            }
        </style>
    `);
});