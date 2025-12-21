/* ==========================================================================
   1. DATA OBJECTS
   ========================================================================== */

const skillData = {
    backend: {
        id: "backend",
        title: "Backend Engineering",
        iconClass: "fas fa-server text-blue-600",
        desc: "My main focus. Heavy emphasis on Python and Java environments.",
        core: ["Python (FastAPI, Django, Flask)", "Java (Spring Boot)"],
        exposure: ["C#", "PHP"]
    },
    databaseAndTools: {
        id: "databaseAndTools",
        title: "Database & DevOps",
        iconClass: "fas fa-database text-green-600",
        desc: "Managing data persistence and deployment workflows.",
        core: ["Git", "Docker", "SQL"],
        exposure: []
    },
    frontend: {
        id: "frontend",
        title: "Frontend",
        iconClass: "fas fa-laptop-code text-purple-500",
        desc: "Basic integration logic to connect user interfaces with backends.",
        core: ["HTML/CSS", "API Integration"],
        exposure: []
    }
};

const experienceData = {
    trailstone: {
        company: "TrailStone",
        period: "Sligo | Apr 2023 – Aug 2023",
        role: "Software Engineering Intern",
        timeline: [
            { title: "Legacy Migration", desc: "Rewrote legacy UI tools using FastAPI and React." },
            { title: "Data Visualization", desc: "Improved market data visualization for traders, increasing data accessibility." },
            { title: "Agile Workflow", desc: "Participated in daily stand-ups and sprint planning using Jira." }
        ]
    },
    wineflair: {
        company: "Wineflair",
        period: "Various Locations | May 2018 – Present",
        role: "Management & Sales",
        timeline: [
            { title: "Leadership", desc: "Rose through the ranks from Sales Assistant to Assistant Manager." },
            { title: "Operations", desc: "Managed stock control, cash handling, and staff training across 10+ locations." },
            { title: "Customer Service", desc: "Maintained high customer satisfaction scores in a fast-paced retail environment." }
        ]
    }
};

const educationData = {
    ou: {
        degree: "BSc (Hons) Computing & IT",
        university: "The Open University",
        year: "2021 – 2026 (Expected)",
        modules: {
            "Stage 1": [
                { code: "TM111", title: "Introduction to Computing and IT Part 1" },
                { code: "TM112", title: "Introduction to Computing and IT Part 2" },
                { code: "TM129", title: "Technologies in Practice" },
                { code: "MU123", title: "Discovering Mathematics" }
            ],
            "Stage 2": [
                { code: "TT284", title: "Web Technologies" },
                { code: "M250", title: "Object-Oriented Java Programming" },
                { code: "M269", title: "Algorithms, Data Structures and Computability" },
                { code: "TM254", title: "Managing IT" }
            ],
            "Stage 3": [
                { code: "TM352", title: "Web, Mobile and Cloud Technologies" },
                { code: "TM356", title: "Interaction Design and the User Experience" },
                { code: "TM354", title: "Software Engineering" },
                { code: "TM470", title: "The Computing and IT Project" }
            ]
        }
    }
};

const projectData = {
    laochra: {
        title: "Laochra 2D Game",
        stack: ["Python", "Pygame"],
        desc: "A top-down 2D adventure game featuring custom sprite animation, collision detection, and state management. Built entirely in Python using the Pygame library to demonstrate OOP principles.",
        link: "https://github.com/CiaranC968"
    },
    tacocloud: {
        title: "TacoCloud",
        stack: ["Java", "Spring Boot", "H2 Database"],
        desc: "A full-stack application allowing users to design custom tacos. Features Spring Security for authentication, Spring Data JPA for persistence, and a REST API for the frontend.",
        link: "https://github.com/CiaranC968"
    }
};

const certData = {
    kainos_event: {
        title: "Open Uni & Kainos Event",
        issuer: "Kainos / Open University",
        date: "2023",
        icon: '<img src="/static/images/ou-cert.png" alt="Cert" class="h-32 mx-auto rounded-lg shadow-md">',
        desc: "Participated in a 2-day intensive industry workshop focused on software delivery, agile practices, and modern cloud technologies. Collaborated with a team to solve real-world coding challenges.",
        link: "#"
    }
};

/* ==========================================================================
   2. RENDERING FUNCTIONS
   ========================================================================== */

function renderSkills() {
    const container = document.getElementById('skills-container');
    if (!container) return;

    container.innerHTML = Object.values(skillData).map(skill => `
        <article onclick="window.openSkillModal('${skill.id}')" 
                 class="card-hover cursor-pointer bg-gray-50 dark:bg-gray-900/50 p-8 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm group hover:shadow-lg transition-all">
            <div class="flex justify-between items-start mb-6">
                <i class="${skill.iconClass} text-5xl group-hover:scale-110 transition-transform"></i>
                <i class="fas fa-arrow-right text-gray-300 group-hover:text-brand-accent -rotate-45 group-hover:rotate-0 transition-all duration-300 text-xl"></i>
            </div>
            <h3 class="text-2xl font-bold mb-3 text-gray-900 dark:text-white group-hover:text-brand-accent transition-colors">
                ${skill.title}
            </h3>
            <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed mb-4">
                ${skill.desc}
            </p>
        </article>
    `).join('');
}

/* ==========================================================================
   3. MODAL LOGIC (Generic & Specific)
   ========================================================================== */

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.firstElementChild.classList.remove('scale-95', 'opacity-0');
        modal.firstElementChild.classList.add('scale-100', 'opacity-100');
    }, 10);
    document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.firstElementChild.classList.remove('scale-100', 'opacity-100');
    modal.firstElementChild.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }, 300);
}

// --- Specific Modal Handlers ---

// 1. Skills
window.openSkillModal = (key) => {
    const data = skillData[key];
    if (!data) return;

    document.getElementById('skillModalTitle').innerText = data.title;
    document.getElementById('skillModalDesc').innerText = data.desc;
    document.getElementById('skillModalIcon').innerHTML = `<i class="${data.iconClass}"></i>`;

    document.getElementById('skillModalCore').innerHTML = data.core.map(item =>
        `<span class="bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 px-3 py-1 rounded-lg text-sm font-medium border border-gray-200 dark:border-gray-600">${item}</span>`
    ).join('');

    const toolsContainer = document.getElementById('skillModalTools');
    const secondHeader = document.getElementById('skillSecondHeader');

    if (data.exposure && data.exposure.length > 0) {
        secondHeader.innerText = "Exposure / Familiar With";
        secondHeader.classList.remove('hidden');
        toolsContainer.innerHTML = data.exposure.map(item =>
            `<span class="bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-3 py-1 rounded-lg text-sm border border-gray-200 dark:border-gray-700">${item}</span>`
        ).join('');
    } else {
        secondHeader.classList.add('hidden');
        toolsContainer.innerHTML = '';
    }
    openModal('skillModal');
};
window.closeSkillModal = () => closeModal('skillModal');

// 2. Experience
window.openExpModal = (key) => {
    const data = experienceData[key];
    if (!data) return;

    document.getElementById('expModalCompany').innerText = data.company;
    document.getElementById('expModalPeriod').innerText = `${data.role} | ${data.period}`;

    document.getElementById('expModalTimeline').innerHTML = data.timeline.map(item => `
        <div class="relative">
            <div class="absolute -left-[41px] top-1 h-5 w-5 rounded-full border-4 border-white dark:border-gray-800 bg-brand-accent"></div>
            <h4 class="text-xl font-bold text-gray-900 dark:text-white mb-1">${item.title}</h4>
            <p class="text-gray-600 dark:text-gray-400 leading-relaxed">${item.desc}</p>
        </div>
    `).join('');
    openModal('experienceModal');
};
window.closeExpModal = () => closeModal('experienceModal');

// 3. Education
window.openEduModal = (key) => {
    const data = educationData[key];
    if (!data) return;

    // 1. Set Header Info
    document.getElementById('eduModalDegree').innerText = data.degree;
    document.getElementById('eduModalUni').innerText = data.university;
    document.getElementById('eduModalYear').innerText = data.year;

    // 2. Prepare Container
    const container = document.getElementById('eduModalModules');

    container.className = "space-y-6";

    let contentHtml = '';

    // 3. Loop through Stages
    for (const [stageName, modules] of Object.entries(data.modules)) {
        contentHtml += `
            <div class="bg-gray-50 dark:bg-gray-900/50 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
                
                <div class="flex items-center gap-3 mb-4 border-b border-gray-200 dark:border-gray-700 pb-3">
                    <span class="bg-brand-accent text-black text-xs font-black px-2 py-1 rounded uppercase tracking-wider">
                        ${stageName}
                    </span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    ${modules.map(mod => `
                        <div class="flex items-start gap-3 p-2 rounded-lg hover:bg-white dark:hover:bg-gray-800 transition-colors">
                            <i class="fas fa-check-circle text-brand-accent mt-1 text-sm flex-shrink-0"></i>
                            <div class="leading-tight">
                                <span class="text-xs font-bold text-gray-400 block mb-0.5">${mod.code}</span>
                                <span class="text-sm font-semibold text-gray-800 dark:text-gray-200">${mod.title}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>

            </div>
        `;
    }

    container.innerHTML = contentHtml;
    openModal('eduModal');
};
window.closeEduModal = () => closeModal('eduModal');


// 4. Certificates
window.openCertModal = (key) => {
    const data = certData[key];
    if (!data) return;

    document.getElementById('certTitle').innerText = data.title;
    document.getElementById('certIssuer').innerText = data.issuer;
    document.getElementById('certDate').innerText = data.date;
    document.getElementById('certDesc').innerText = data.desc;
    document.getElementById('certIcon').innerHTML = data.icon;
    document.getElementById('certLink').href = data.link;

    openModal('certModal');
};
window.closeCertModal = () => closeModal('certModal');

// 5. Projects (Event Listener approach used for these)
function setupProjectModals() {
    const cards = document.querySelectorAll('.project-card');
    cards.forEach(card => {
        card.addEventListener('click', () => {
            const key = card.getAttribute('data-project');
            const data = projectData[key];
            if (!data) return;

            document.getElementById('modalTitle').innerText = data.title;
            document.getElementById('modalDescription').innerText = data.desc;
            document.getElementById('modalLink').href = data.link;

            document.getElementById('modalStack').innerHTML = data.stack.map(tech =>
                `<span class="bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded text-sm font-bold text-gray-600 dark:text-gray-300">${tech}</span>`
            ).join('');

            openModal('projectModal');
        });
    });
}

/* ==========================================================================
   4. INITIALIZATION & UI UTILITIES
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

    // A. Render Dynamic Content
    renderSkills();
    setupProjectModals();

    // B. Theme Logic
    const toggleFixed = document.getElementById('theme-toggle-fixed');
    const toggleMobile = document.getElementById('theme-btn-mobile');

    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
        if(toggleFixed) toggleFixed.checked = true;
    } else {
        document.documentElement.classList.remove('dark');
        if(toggleFixed) toggleFixed.checked = false;
    }

    const toggleTheme = () => {
        document.documentElement.classList.toggle('dark');
        localStorage.theme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    };

    if(toggleFixed) toggleFixed.addEventListener('change', toggleTheme);
    if(toggleMobile) toggleMobile.addEventListener('click', toggleTheme);

    // C. Mobile Menu
    const menuBtn = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    function toggleMenu() {
        const isClosed = sidebar.classList.contains('-translate-x-full');
        if (isClosed) {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.remove('hidden');
            setTimeout(() => overlay.classList.remove('opacity-0'), 10);
        } else {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('opacity-0');
            setTimeout(() => overlay.classList.add('hidden'), 300);
        }
    }

    if(menuBtn) menuBtn.addEventListener('click', toggleMenu);
    if(overlay) overlay.addEventListener('click', toggleMenu);

    // D. Scroll to Top
    const scrollBtn = document.getElementById('scrollTopBtn');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            scrollBtn.classList.remove('hidden');
        } else {
            scrollBtn.classList.add('hidden');
        }
    });
    if(scrollBtn) {
        scrollBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // E. Resume Modal
    const openCvBtn = document.getElementById('openCvModal');
    const closeCvBtn = document.getElementById('closeCvModal');
    if(openCvBtn) openCvBtn.addEventListener('click', () => openModal('cvModal'));
    if(closeCvBtn) closeCvBtn.addEventListener('click', () => closeModal('cvModal'));

    // F. Project Modal Close Btn
    const closeProjBtn = document.getElementById('closeProjectModal');
    if(closeProjBtn) closeProjBtn.addEventListener('click', () => closeModal('projectModal'));

    /* ==========================================================================
       G. Global Modal Utilities (Escape Key & Click Outside)
       ========================================================================== */

    // 1. Close on Escape Key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.fixed.inset-0:not(.hidden)');
            openModals.forEach(modal => {
                // Skip the sidebar overlay, only close content modals
                if (modal.id !== 'sidebar-overlay') {
                    closeModal(modal.id);
                }
            });
        }
    });

    const allModals = [
        'cvModal', 'projectModal', 'experienceModal',
        'skillModal', 'eduModal', 'certModal'
    ];

    allModals.forEach(id => {
        const modal = document.getElementById(id);
        if (modal) {
            modal.addEventListener('click', (e) => {

                if (e.target === modal) {
                    closeModal(id);
                }
            });
        }
    });

});