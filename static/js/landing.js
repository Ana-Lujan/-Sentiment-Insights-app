// Landing Page Interactive Elements - Sentiment Insights

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive features
    initSmoothScrolling();
    initCounterAnimation();
    initScrollAnimations();
    initNavbarScroll();
    initDemoPreview();
});

// Smooth scrolling for navigation links
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 70; // Account for fixed navbar

                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Animated counter for statistics
function initCounterAnimation() {
    const counters = document.querySelectorAll('.stat-number');

    const animateCounter = (counter) => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 2000; // 2 seconds
        const step = target / (duration / 16); // 60 FPS
        let current = 0;

        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current);
            }
        }, 16);
    };

    // Intersection Observer to trigger animation when visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));
}

// Scroll animations for sections
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe all sections
    const sections = document.querySelectorAll('section');
    sections.forEach(section => observer.observe(section));

    // Observe feature cards
    const featureCards = document.querySelectorAll('.feature-card, .case-card, .engine-card, .metric-card');
    featureCards.forEach(card => observer.observe(card));
}

// Navbar background change on scroll
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');

    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
}

// Interactive demo preview
function initDemoPreview() {
    const results = document.querySelectorAll('.analysis-result');
    let currentIndex = 0;

    // Auto-rotate demo results
    setInterval(() => {
        results.forEach((result, index) => {
            result.style.opacity = index === currentIndex ? '1' : '0.3';
        });
        currentIndex = (currentIndex + 1) % results.length;
    }, 3000);

    // Add click interaction
    results.forEach(result => {
        result.addEventListener('click', () => {
            // Add pulse animation
            result.style.animation = 'pulse 0.6s ease';
            setTimeout(() => {
                result.style.animation = '';
            }, 600);
        });
    });
}

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    .animate-in {
        animation: fadeInUp 0.8s ease-out forwards;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .navbar-scrolled {
        background: rgba(10, 10, 10, 0.98) !important;
        box-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
    }

    /* Hover effects for interactive elements */
    .feature-card:hover .feature-icon,
    .case-card:hover .case-icon,
    .engine-card:hover .engine-icon {
        transform: scale(1.1);
        transition: transform 0.3s ease;
    }

    .tech-item:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }

    .tech-item:hover span {
        color: white !important;
    }
`;
document.head.appendChild(style);

// Performance optimization - lazy load images
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading
lazyLoadImages();

// Add loading states for buttons
function addLoadingStates() {
    const buttons = document.querySelectorAll('.btn');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.href && this.href.includes('/demo')) {
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Cargando Demo...';
                this.style.pointerEvents = 'none';
            }
        });
    });
}

// Initialize loading states
addLoadingStates();

// Track user engagement
function trackEngagement() {
    let timeOnPage = 0;

    const timeTracker = setInterval(() => {
        timeOnPage += 1;

        // Send engagement data (could be used for analytics)
        if (timeOnPage % 10 === 0) { // Every 10 seconds
            console.log(`User engaged for ${timeOnPage} seconds`);
        }
    }, 1000);

    // Track scroll depth
    let maxScroll = 0;
    window.addEventListener('scroll', () => {
        const scrollPercent = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        if (scrollPercent > maxScroll) {
            maxScroll = scrollPercent;
            if (maxScroll > 25 && maxScroll <= 50) {
                console.log('25% scroll reached');
            } else if (maxScroll > 50 && maxScroll <= 75) {
                console.log('50% scroll reached');
            } else if (maxScroll > 75) {
                console.log('75% scroll reached - high engagement!');
            }
        }
    });
}

// Initialize engagement tracking
trackEngagement();

// Add keyboard navigation
document.addEventListener('keydown', (e) => {
    // Space bar to scroll to next section
    if (e.code === 'Space') {
        e.preventDefault();
        const sections = document.querySelectorAll('section');
        const currentScroll = window.scrollY;
        const windowHeight = window.innerHeight;

        for (let section of sections) {
            const sectionTop = section.offsetTop - 70;
            if (sectionTop > currentScroll + windowHeight * 0.5) {
                window.scrollTo({
                    top: sectionTop,
                    behavior: 'smooth'
                });
                break;
            }
        }
    }
});

// Console welcome message
console.log(`
🧠 Sentiment Insights - Landing Page Loaded
===========================================
✅ Interactive elements initialized
✅ Animations ready
✅ Analytics tracking active
✅ Performance optimized

Navigate with keyboard (Space) or scroll naturally!
`);