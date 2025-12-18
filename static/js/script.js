document.addEventListener("DOMContentLoaded", function () {
        // Sidebar visibility logic for desktop
        const sidebarName = document.getElementById("sidebar-name");
        const aboutSection = document.getElementById("about");
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        sidebarName.classList.add("hidden");
                    } else {
                        sidebarName.classList.remove("hidden");
                    }
                });
            },
            { threshold: 0.5 }
        );
        observer.observe(aboutSection);

        // Mobile menu toggle logic
        const menuToggle = document.getElementById('menu-toggle');
        const sidebar = document.getElementById('sidebar');
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('hidden');
        });
        // Hide sidebar when a link is clicked
        const sidebarLinks = document.querySelectorAll('#sidebar a');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth < 768) {
                    sidebar.classList.add('hidden');
                }
            });
        });

        // CV Modal logic
        const openCvModal = document.getElementById('openCvModal');
        const closeCvModal = document.getElementById('closeCvModal');
        const cvModal = document.getElementById('cvModal');

        function openModal() {
            cvModal.classList.remove('hidden');
            document.documentElement.style.overflow = 'hidden';
        }
        function closeModal() {
            cvModal.classList.add('hidden');
            document.documentElement.style.overflow = '';
        }

        openCvModal.addEventListener('click', openModal);
        closeCvModal.addEventListener('click', closeModal);
        cvModal.addEventListener('click', (e) => {
            if (e.target === cvModal) closeModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !cvModal.classList.contains('hidden')) closeModal();
        });
    });
