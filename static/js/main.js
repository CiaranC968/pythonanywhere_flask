/* ==========================================================================
   1. Data Objects (Experience & Projects)
   ========================================================================== */

const experienceData = {
    wineflair: {
        company: "Wineflair",
        overallPeriod: "May 2018 – Present",
        roles: [
            {
                title: "Assistant Manager",
                date: "Sept 2023 – Present",
                location: "Various Locations",
                desc: "Leading operations, staff management, and ensuring operational excellence across multiple locations. Responsible for KPI tracking and team development."
            },
            {
                title: "Assistant Manager",
                date: "April 2019 – April 2023",
                location: "Portadown",
                desc: "Managed store operations across 10 locations, overseeing cash operations, inventory control, and shift scheduling. Reduced wastage by 15% through better stock management."
            },
            {
                title: "Sales Assistant",
                date: "May 2018 – June 2019",
                location: "Coalisland",
                desc: "Provided exceptional customer service, managed inventory in diverse locations, and assisted with visual merchandising."
            }
        ]
    },
    trailstone: {
        company: "TrailStone",
        overallPeriod: "April 2023 – Aug 2023",
        roles: [
            {
                title: "Software Engineering Intern",
                date: "April 2023 – Aug 2023",
                location: "Sligo",
                desc: "Rewrote legacy UI tools using FastAPI and React. Integrated real-time market data visualization for traders, improving decision-making speed. Collaborated with senior engineers on backend microservices."
            }
        ]
    }
};

const projectData = {
    laochra: {
        title: "Laochra 2D Game",
        stack: ["Python", "Pygame"],
        description: "A Viking-themed 2D adventure game built with Pygame. Features include custom sprite animation, collision detection, and a state-management system for game levels.",
        link: "https://github.com/CiaranC968/Laochra"
    },
    tacocloud: {
        title: "TacoCloud",
        stack: ["Java", "Spring Boot", "H2 Database"],
        description: "A full-stack application allowing users to design custom tacos. Built with Spring Boot for the backend and Thymeleaf for templating, featuring secure login and order persistence.",
        link: "https://github.com/CiaranC968/TacoCloud"
    }
};


/* ==========================================================================
   2. Theme Toggling Logic (Dark Mode)
   ========================================================================== */

const fixedToggle = document.getElementById('theme-toggle-fixed'); // Top right
const slideToggle = document.getElementById('theme-toggle-slide'); // Mobile sidebar
const html = document.documentElement;

function applyTheme(isDark) {
    if (isDark) {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    } else {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    }
    // Sync both checkboxes
    if(fixedToggle) fixedToggle.checked = isDark;
    if(slideToggle) slideToggle.checked = isDark;
}

// Event Listeners for Theme
if(fixedToggle) {
    fixedToggle.addEventListener('change', (e) => applyTheme(e.target.checked));
}
if(slideToggle) {
    slideToggle.addEventListener('change', (e) => applyTheme(e.target.checked));
}

// Initialize Theme on Load
const savedTheme = localStorage.getItem('theme');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
applyTheme(savedTheme === 'dark' || (!savedTheme && systemDark));


/* ==========================================================================
   3. Mobile Sidebar Logic
   ========================================================================== */

const menuToggle = document.getElementById('menu-toggle');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebar-overlay');
const navLinks = document.querySelectorAll('#sidebar nav a');

function toggleSidebar() {
    sidebar.classList.toggle('-translate-x-full');
    overlay.classList.toggle('hidden');
}

if(menuToggle) {
    menuToggle.addEventListener('click', toggleSidebar);
    overlay.addEventListener('click', toggleSidebar);
    
    // Close sidebar when a link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (!sidebar.classList.contains('-translate-x-full')) {
                toggleSidebar();
            }
        });
    });
}


/* ==========================================================================
   4. Experience Modal Logic
   ========================================================================== */

const expModal = document.getElementById('experienceModal');
const expTitle = document.getElementById('expModalCompany');
const expPeriod = document.getElementById('expModalPeriod');
const expTimeline = document.getElementById('expModalTimeline');

// Exposed to global scope for HTML onclick
window.openExpModal = function(companyKey) {
    const data = experienceData[companyKey];
    if(!data) return;

    // Set Header Info
    expTitle.textContent = data.company;
    expPeriod.textContent = data.overallPeriod;

    // Build Timeline HTML
    let htmlContent = '';
    data.roles.forEach(role => {
        htmlContent += `
            <div class="relative">
                <span class="absolute -left-[39px] top-1 h-4 w-4 rounded-full border-4 border-white dark:border-gray-800 bg-brand-accent"></span>
                <h4 class="text-xl font-bold text-gray-900 dark:text-white">${role.title}</h4>
                <div class="flex flex-col sm:flex-row sm:justify-between text-sm text-gray-500 mb-3 italic">
                    <span>${role.date}</span>
                    <span>${role.location}</span>
                </div>
                <p class="text-gray-600 dark:text-gray-300 leading-relaxed">${role.desc}</p>
            </div>
        `;
    });

    expTimeline.innerHTML = htmlContent;
    expModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent scrolling
};

window.closeExpModal = function() {
    expModal.classList.add('hidden');
    document.body.style.overflow = '';
};

// Close on outside click
if(expModal) {
    expModal.addEventListener('click', (e) => {
        if (e.target === expModal) window.closeExpModal();
    });
}


/* ==========================================================================
   5. Project Modal Logic
   ========================================================================== */

const projectModal = document.getElementById('projectModal');
const closeProjectBtn = document.getElementById('closeProjectModal');
const projectCards = document.querySelectorAll('.project-card');

projectCards.forEach(card => {
    card.addEventListener('click', () => {
        const projectId = card.dataset.project;
        const data = projectData[projectId];

        if (data) {
            document.getElementById('modalTitle').innerText = data.title;
            document.getElementById('modalDescription').innerText = data.description;
            document.getElementById('modalLink').href = data.link;

            // Generate tech badges
            const stackContainer = document.getElementById('modalStack');
            stackContainer.innerHTML = data.stack.map(tech => 
                `<span class="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1 rounded-lg text-sm font-semibold">${tech}</span>`
            ).join('');

            projectModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    });
});

if(closeProjectBtn) {
    closeProjectBtn.addEventListener('click', () => {
        projectModal.classList.add('hidden');
        document.body.style.overflow = '';
    });
    
    projectModal.addEventListener('click', (e) => {
        if (e.target === projectModal) {
            projectModal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    });
}


/* ==========================================================================
   6. CV Modal Logic
   ========================================================================== */

const cvModal = document.getElementById('cvModal');
const openCvBtn = document.getElementById('openCvModal'); // The button in "About" section
const closeCvBtn = document.getElementById('closeCvModal'); // The 'X' inside the modal

if (openCvBtn && cvModal) {
    openCvBtn.addEventListener('click', (e) => {
        e.preventDefault(); // Stop it from following the link if you used an <a> tag
        cvModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    });
}

if (closeCvBtn && cvModal) {
    closeCvBtn.addEventListener('click', () => {
        cvModal.classList.add('hidden');
        document.body.style.overflow = '';
    });

    // Close when clicking the dark background
    cvModal.addEventListener('click', (e) => {
        if (e.target === cvModal) {
            cvModal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    });
}


/* ==========================================================================
   7. Scroll to Top Logic
   ========================================================================== */

const scrollTopBtn = document.getElementById('scrollTopBtn');

window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
        scrollTopBtn.classList.remove('hidden');
    } else {
        scrollTopBtn.classList.add('hidden');
    }
});

if(scrollTopBtn) {
    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

/* ==========================================================================
   8. Skill Modal Logic (New)
   ========================================================================== */

const skillData = {
    python: {
        title: "Python Ecosystem",
        icon: '<i class="fab fa-python text-blue-500"></i>',
        desc: "My primary language for backend logic and data processing.",
        core: ["Python 3.10+", "FastAPI", "Flask", "Django"],
        tools: ["Pandas", "NumPy", "SQLAlchemy", "Pytest", "Poetry", "Celery", "Jupyter"]
    },
    java: {
        title: "Java Engineering",
        icon: '<i class="fab fa-java text-red-500"></i>',
        desc: "Building robust, enterprise-grade backend systems.",
        core: ["Java 17", "Spring Boot", "Spring Security", "JPA / Hibernate"],
        tools: ["Maven", "Gradle", "JUnit 5", "Mockito", "Lombok", "Docker", "PostgreSQL"]
    },
    frontend: {
        title: "Frontend & Web",
        icon: '<i class="fab fa-react text-blue-400"></i>',
        desc: "Creating responsive and interactive user interfaces.",
        core: ["TypeScript", "React 18", "JavaScript (ES6+)", "HTML5 / CSS3"],
        tools: ["Tailwind CSS", "Redux Toolkit", "React Router", "Vite", "Axios", "Framer Motion", "Git"]
    }
};

const skillModal = document.getElementById('skillModal');
const skillTitle = document.getElementById('skillModalTitle');
const skillIcon = document.getElementById('skillModalIcon');
const skillDesc = document.getElementById('skillModalDesc');
const skillCore = document.getElementById('skillModalCore');
const skillTools = document.getElementById('skillModalTools');

window.openSkillModal = function(key) {
    const data = skillData[key];
    if(!data) return;

    // Populate Header
    skillTitle.textContent = data.title;
    skillIcon.innerHTML = data.icon;
    skillDesc.textContent = data.desc;

    // Generate Core Badges
    skillCore.innerHTML = data.core.map(item => 
        `<span class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl font-bold text-sm shadow-sm">${item}</span>`
    ).join('');

    // Generate Tool Badges
    skillTools.innerHTML = data.tools.map(item => 
        `<span class="px-3 py-1.5 bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 rounded-lg text-xs font-medium">${item}</span>`
    ).join('');

    skillModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
};

window.closeSkillModal = function() {
    skillModal.classList.add('hidden');
    document.body.style.overflow = '';
};

// Close on outside click
if(skillModal) {
    skillModal.addEventListener('click', (e) => {
        if (e.target === skillModal) window.closeSkillModal();
    });
}



/* ==========================================================================
   9. Education Modal Logic (Updated)
   ========================================================================== */

const educationData = {
    ou: {
        degree: "BSc (Hons) Computing & IT",
        university: "Open University",
        year: "2021 – 2026 (Expected)",
        stages: {
            "Stage 1 (First Year)": [
                { code: "TM111", title: "Introduction to Computing & IT 1" },
                { code: "TM112", title: "Introduction to Computing & IT 2" },
                { code: "TM129", title: "Technologies in Practice" },
                { code: "MU123", title: "Discovering Mathematics" }
            ],
            "Stage 2 (Second Year)": [
                { code: "TT284", title: "Web Technologies" },
                { code: "M250", title: "Object-Oriented Java Programming" },
                { code: "M269", title: "Algorithms, Data Structures & Computability" },
                { code: "TM254", title: "Managing IT" }
            ],
            "Stage 3 (Final Year)": [
                { code: "TM352", title: "Web, Mobile and Cloud Technologies" },
                { code: "TM351", title: "Data Management and Analysis" },
                { code: "TM354", title: "Software Engineering" },
                { code: "TM470", title: "The Computing and IT Project" }
            ]
        }
    }
};

const eduModal = document.getElementById('eduModal');
const eduDegree = document.getElementById('eduModalDegree');
const eduUni = document.getElementById('eduModalUni');
const eduYear = document.getElementById('eduModalYear');
const eduModules = document.getElementById('eduModalModules');

window.openEduModal = function(key) {
    const data = educationData[key];
    if(!data) return;

    eduDegree.textContent = data.degree;
    eduUni.textContent = data.university;
    eduYear.textContent = data.year;

    // Build the Stage-based Grid
    let contentHtml = '';
    
    // Loop through each stage (Stage 1, Stage 2, Stage 3)
    for (const [stageName, modules] of Object.entries(data.stages)) {
        contentHtml += `
            <div class="mb-8 last:mb-0">
                <h4 class="text-sm font-bold uppercase tracking-widest text-brand-accent mb-4 border-b border-gray-100 dark:border-gray-700 pb-2">
                    ${stageName}
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${modules.map(mod => `
                        <div class="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-xl border border-gray-100 dark:border-gray-700 flex items-center gap-4 hover:border-brand-accent transition-colors">
                            <span class="font-mono text-sm font-bold text-gray-400 bg-white dark:bg-gray-800 px-2 py-1 rounded border border-gray-200 dark:border-gray-600">
                                ${mod.code}
                            </span>
                            <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">
                                ${mod.title}
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    eduModules.innerHTML = contentHtml;
    
    // Update Layout for Scrolling
    eduModules.className = ''; // Remove grid class as we are handling layout inside the loop now

    eduModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
};

window.closeEduModal = function() {
    eduModal.classList.add('hidden');
    document.body.style.overflow = '';
};

// Close on outside click
if(eduModal) {
    eduModal.addEventListener('click', (e) => {
        if (e.target === eduModal) window.closeEduModal();
    });
}


/* ==========================================================================
   10. Certificate Modal Logic (New)
   ========================================================================== */

const certData = {
    
    kainos_event: {
    title: "Open Uni & Kainos Event",
    issuer: "Kainos / Open University",
    date: "Duration: 2 Days",
    // Updated styling: w-full and shadow-xl for a better "preview" look
    icon: '<img src="/static/images/ou-cert.png" alt="Certificate" class="w-full h-auto rounded-xl shadow-xl mb-6 border border-gray-200 dark:border-gray-700">',
    desc: "A collaborative 2-day event hosted by Kainos. Gained practical insight into modern software delivery lifecycles, agile methodologies, and industry-standard development practices.",
    link: "/static/images/ou-cert.png" // The button will now open the image in a new tab
}

};

const certModal = document.getElementById('certModal');
const certTitle = document.getElementById('certTitle');
const certIssuer = document.getElementById('certIssuer');
const certDate = document.getElementById('certDate');
const certDesc = document.getElementById('certDesc');
const certLink = document.getElementById('certLink');
const certIcon = document.getElementById('certIcon');

window.openCertModal = function(key) {
    const data = certData[key];
    if(!data) return;

    certTitle.textContent = data.title;
    certIssuer.textContent = data.issuer;
    certDate.textContent = data.date;
    certDesc.textContent = data.desc;
    certIcon.innerHTML = data.icon;
    certLink.href = data.link;

    certModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
};

window.closeCertModal = function() {
    certModal.classList.add('hidden');
    document.body.style.overflow = '';
};

if(certModal) {
    certModal.addEventListener('click', (e) => {
        if (e.target === certModal) window.closeCertModal();
    });
}