import json
import sqlite3
from urllib.parse import quote_plus

import streamlit as st

from app.database import add_application, add_job, authenticate_user, create_user, init_db, list_applications, list_jobs
from app.documents import extract_text
from app.matching import match_candidate
from app.skills import extract_skills

COMPANY = {
    "address": "100 Market Street, Suite 400, San Francisco, CA 94105",
    "phone": "+1 (415) 555-0147",
    "email": "hello@talentlens.example",
    "hours": "Monday - Friday, 9:00 AM - 6:00 PM PT",
}

JOB_PLATFORMS = [
    ("Google Jobs", "Search the widest web of job listings.", "https://www.google.com/search?q={query}+jobs"),
    ("LinkedIn", "Explore roles and professional connections.", "https://www.linkedin.com/jobs/search/?keywords={query}&location={location}"),
    ("Indeed", "Search broad listings by title and place.", "https://www.indeed.com/jobs?q={query}&l={location}"),
    ("Wellfound", "Find roles at startups and growing teams.", "https://wellfound.com/jobs?query={query}"),
    ("Glassdoor", "Compare openings, companies, and workplace insight.", "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}&locT=C&locId=0"),
    ("Remote OK", "Find remote-first roles around the world.", "https://remoteok.com/remote-{query}-jobs"),
]


def assistant_reply(message: str) -> str:
    """Return helpful local answers without sending customer data to a service."""
    normalized = message.lower()
    if any(word in normalized for word in ["hello", "hi", "hey"]):
        return "Hello. I can help you understand matching, resume analysis, privacy, saved jobs, or how to contact TalentLens."
    if "privacy" in normalized or "data" in normalized or "secure" in normalized:
        return "TalentLens is local-first in this workspace. Resume text, jobs, and applications are stored locally, and the matching calculation runs in the app."
    if "match" in normalized or "score" in normalized or "fit" in normalized:
        return "Open Match workspace, add your resume, paste a job description, and choose Analyze match. The report combines semantic similarity with skill coverage and shows the skills behind the result."
    if "resume" in normalized or "cv" in normalized or "skill" in normalized:
        return "Upload a PDF, DOCX, TXT, or Markdown resume from the profile panel, or paste the text directly. TalentLens extracts recognizable skills before comparing roles."
    if "job" in normalized or "role" in normalized or "application" in normalized:
        return f"You currently have {len(jobs)} saved role(s) and {len(applications)} tracked application(s). Add roles in Job library, then use Track application to keep them visible."
    if "contact" in normalized or "phone" in normalized or "email" in normalized or "address" in normalized:
        return f"You can reach TalentLens at {COMPANY['email']} or {COMPANY['phone']}. Office: {COMPANY['address']}."
    if "about" in normalized or "talentlens" in normalized:
        return "TalentLens is a career intelligence workspace for transparent role matching, skill-gap discovery, and application tracking. Open About TalentLens for the full product overview."
    return "I can help with resume uploads, match scores, skill gaps, saved jobs, applications, privacy, or contacting TalentLens. What would you like to know?"


st.set_page_config(page_title="TalentLens | Career intelligence", page_icon="TL", layout="wide", initial_sidebar_state="expanded")
init_db()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink: #17212b; --muted: #687684; --line: #dfe7e6; --mint: #d9f4e8; --teal: #087f73; --coral: #ed765f; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; }
    .stApp { background: linear-gradient(135deg, #f7fbfa 0%, #ffffff 46%, #fff8f3 100%); }
    header[data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"], #MainMenu, footer { visibility: hidden; }
    [data-testid="stSidebar"] { background: #f1f8f5; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
    .brand { display: flex; align-items: center; gap: .75rem; margin-bottom: 2.3rem; }
    .brand-mark { display: grid; place-items: center; width: 2.6rem; height: 2.6rem; border-radius: 10px; color: white; background: var(--teal); font-family: 'Space Grotesk'; font-weight: 700; }
    .brand-name { font: 700 1.25rem 'Space Grotesk'; letter-spacing: -.04em; }
    .eyebrow { color: var(--teal); font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    .hero { padding: 1.6rem 0 1.2rem; }
    .hero h1 { font-size: clamp(2rem, 4vw, 3.25rem); margin: .35rem 0 .55rem; color: #132c35; }
    .hero p { color: var(--muted); font-size: 1.05rem; max-width: 680px; margin: 0; }
    .section-heading { margin: .6rem 0 1rem; }
    .section-heading h2 { margin: .25rem 0 .2rem; font-size: 1.4rem; }
    .section-heading p { color: var(--muted); margin: 0; font-size: .9rem; }
    .kpi { background: rgba(255,255,255,.82); border: 1px solid var(--line); border-radius: 12px; padding: 1.1rem 1.2rem; min-height: 110px; }
    .kpi-label { color: var(--muted); font-size: .78rem; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
    .kpi-value { color: #132c35; font: 700 1.65rem 'Space Grotesk'; margin-top: .45rem; overflow-wrap: anywhere; }
    .result-panel { background: #ffffff; border: 1px solid var(--line); border-radius: 14px; padding: 1.25rem; margin-top: 1.2rem; }
    .score { color: var(--teal); font: 700 2.6rem 'Space Grotesk'; line-height: 1; }
    .skill-pill { display: inline-block; background: var(--mint); color: #17634e; border-radius: 999px; padding: .3rem .65rem; margin: .2rem .25rem .1rem 0; font-size: .82rem; }
    .gap-pill { display: inline-block; background: #fff0eb; color: #a64c3b; border-radius: 999px; padding: .3rem .65rem; margin: .2rem .25rem .1rem 0; font-size: .82rem; }
    .empty-state { border: 1px dashed #b8cdca; border-radius: 14px; padding: 2.5rem; text-align: center; color: var(--muted); background: rgba(255,255,255,.5); }
    .about-band { background: #132c35; color: #f7fbfa; border-radius: 16px; padding: 1.5rem; margin-top: 1.25rem; }
    .about-band h3 { color: white; margin: .25rem 0 .45rem; }
    .about-band p { color: #c6d9d6; margin: 0; line-height: 1.6; }
    .about-card { background: rgba(255,255,255,.72); border: 1px solid var(--line); border-radius: 12px; padding: 1.1rem; min-height: 145px; }
    .about-card h3 { font-size: 1rem; margin: .35rem 0; }
    .about-card p { color: var(--muted); font-size: .88rem; line-height: 1.5; margin: 0; }
    .step-number { color: var(--coral); font: 700 1.1rem 'Space Grotesk'; }
    .contact-card { background: #ffffff; border: 1px solid var(--line); border-radius: 12px; padding: 1.1rem; min-height: 120px; }
    .contact-card strong { display: block; color: #132c35; margin-bottom: .35rem; }
    .contact-card span { color: var(--muted); font-size: .88rem; line-height: 1.5; }
    .chat-note { background: #eaf7f2; border-left: 4px solid var(--teal); border-radius: 8px; color: #246154; padding: .8rem 1rem; font-size: .9rem; }
    .platform-card { background: rgba(255,255,255,.82); border: 1px solid var(--line); border-radius: 12px; padding: 1.1rem; min-height: 150px; }
    .platform-card h3 { color: #132c35; font-size: 1rem; margin: 0 0 .35rem; }
    .platform-card p { color: var(--muted); font-size: .85rem; line-height: 1.5; min-height: 42px; }
    .platform-link { color: var(--teal); font-weight: 700; text-decoration: none; font-size: .88rem; }
    .auth-shell { max-width: 1080px; margin: 4rem auto 0; }
    .auth-panel { background: rgba(255,255,255,.9); border: 1px solid var(--line); border-radius: 18px; padding: 2rem; box-shadow: 0 20px 50px rgba(19,44,53,.08); }
    .auth-panel h1 { color: #132c35; font-size: 2rem; margin: .4rem 0 .5rem; }
    .auth-panel p { color: var(--muted); line-height: 1.55; }
    .auth-side { background: #132c35; border-radius: 16px; color: white; padding: 2rem; min-height: 380px; }
    .auth-side h2 { color: white; margin: .5rem 0 1rem; }
    .auth-side p { color: #c6d9d6; }
    .auth-check { color: #d9f4e8; margin: 1rem 0; }
    .user-chip { background: #eaf7f2; border: 1px solid #c9e7dc; border-radius: 999px; color: #246154; padding: .45rem .75rem; font-size: .82rem; }
    .stButton > button[kind="primary"] { background: var(--teal); border-color: var(--teal); }
    .stButton > button[kind="primary"]:hover { background: #05665d; border-color: #05665d; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

if not st.session_state.authenticated_user:
    auth_left, auth_right = st.columns([1.05, 1], gap="large")
    with auth_left:
        st.markdown('<div class="auth-shell"><div class="auth-panel"><div class="brand"><div class="brand-mark">TL</div><div class="brand-name">TalentLens</div></div><div class="eyebrow">Welcome back</div><h1>Build a smarter career path.</h1><p>Sign in to keep your profile, matches, saved jobs, and applications together in one private workspace.</p></div></div>', unsafe_allow_html=True)
    with auth_right:
        st.markdown('<div class="auth-shell"><div class="auth-side"><div class="eyebrow">Career intelligence, focused</div><h2>Your job search, with more signal.</h2><p>TalentLens helps you understand your fit, discover better opportunities, and move applications forward.</p><div class="auth-check">✓ Explainable match reports</div><div class="auth-check">✓ Local-first profile workspace</div><div class="auth-check">✓ One place for every opportunity</div></div></div>', unsafe_allow_html=True)
    sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])
    with sign_in_tab:
        with st.form("sign_in"):
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            if st.form_submit_button("Sign in", type="primary", use_container_width=True):
                if not email or not password:
                    st.warning("Enter your email and password to continue.")
                else:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.authenticated_user = user
                        st.rerun()
                    else:
                        st.error("We could not sign you in with those details.")
    with sign_up_tab:
        with st.form("sign_up"):
            name = st.text_input("Full name", placeholder="Alex Morgan")
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Create password", type="password", placeholder="At least 8 characters")
            confirm_password = st.text_input("Confirm password", type="password")
            if st.form_submit_button("Create account", type="primary", use_container_width=True):
                if not name or not email or not password or not confirm_password:
                    st.warning("Complete every field to create your account.")
                elif len(password) < 8:
                    st.warning("Use a password with at least 8 characters.")
                elif password != confirm_password:
                    st.warning("Your passwords do not match.")
                else:
                    try:
                        st.session_state.authenticated_user = create_user(name, email, password)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("An account with that email already exists. Try signing in instead.")
    st.caption("By continuing, you agree to use TalentLens for your own career planning. Your local workspace data stays on this machine.")
    st.stop()

jobs = list_jobs()
applications = list_applications()

st.markdown('<div class="hero"><div class="eyebrow">Career intelligence workspace</div><h1>Make your next move count.</h1><p>See how your experience maps to the roles you want, close the right skill gaps, and keep every application moving.</p></div>', unsafe_allow_html=True)

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">TL</div><div class="brand-name">TalentLens</div></div>', unsafe_allow_html=True)
    user = st.session_state.authenticated_user
    st.markdown(f'<div class="user-chip">Signed in as {user["name"]}</div>', unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        st.session_state.authenticated_user = None
        st.session_state.resume_text = ""
        st.rerun()
    st.divider()
    st.markdown('<div class="eyebrow">Your profile</div>', unsafe_allow_html=True)
    st.caption("Add your resume once. TalentLens keeps the analysis local and transparent.")
    upload = st.file_uploader("Upload resume", type=["pdf", "docx", "txt", "md"])
    if upload:
        try:
            st.session_state.resume_text = extract_text(upload.name, upload.getvalue())
            st.success(f"Loaded {upload.name}")
        except ValueError as error:
            st.error(str(error))
    resume_text = st.text_area("Resume text", value=st.session_state.resume_text, height=220)
    st.session_state.resume_text = resume_text
    if resume_text:
        st.success(f"{len(extract_skills(resume_text))} skills ready for matching")
    else:
        st.info("Your profile is waiting for a resume")
    st.divider()
    st.caption("Your workspace is local-first: resume text and saved roles stay in this app's local database.")

profile_skills = extract_skills(st.session_state.resume_text)
metric_columns = st.columns(4)
for column, label, value in zip(
    metric_columns,
    ["Profile skills", "Saved roles", "Tracked applications", "Next action"],
    [str(len(profile_skills)), str(len(jobs)), str(len(applications)), "Find your fit" if resume_text else "Add your resume"],
):
    column.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

analyze_tab, jobs_tab, finder_tab, tracker_tab, about_tab, assistant_tab = st.tabs(["Match workspace", "Job library", "Find jobs", "Application tracker", "About TalentLens", "AI assistant"])

with analyze_tab:
    st.markdown('<div class="section-heading"><div class="eyebrow">01 / Match workspace</div><h2>Compare yourself to a role</h2><p>Turn a job description into a clear, evidence-based fit report.</p></div>', unsafe_allow_html=True)
    job_description = st.text_area("Job description", height=210, placeholder="Paste the complete role description here...", label_visibility="collapsed")
    if st.button("Analyze match", type="primary", disabled=not resume_text or not job_description):
        result = match_candidate(resume_text, job_description)
        st.markdown('<div class="result-panel">', unsafe_allow_html=True)
        left, middle, right = st.columns([1.15, 1, 1])
        left.markdown(f'<div class="kpi-label">Overall fit</div><div class="score">{result["score"]}%</div>', unsafe_allow_html=True)
        middle.metric("Semantic fit", f"{result['semantic_score']}%")
        right.metric("Skill coverage", f"{result['skill_score']}%")
        st.progress(result["score"] / 100, text="Match confidence")
        matched, missing = st.columns(2)
        with matched:
            st.markdown("#### Strengths in your profile")
            skills = result["matching_skills"]
            st.markdown("".join(f'<span class="skill-pill">{skill}</span>' for skill in skills) or "No known skills matched", unsafe_allow_html=True)
        with missing:
            st.markdown("#### Skills to strengthen")
            gaps = result["missing_skills"]
            st.markdown("".join(f'<span class="gap-pill">{skill}</span>' for skill in gaps) or "No gaps detected", unsafe_allow_html=True)
        st.download_button("Download match report", json.dumps(result, indent=2), "match-report.json", "application/json", icon=" :material/download:")
        st.markdown('</div>', unsafe_allow_html=True)

with jobs_tab:
    st.markdown('<div class="section-heading"><div class="eyebrow">02 / Job library</div><h2>Roles worth your attention</h2><p>Save opportunities here and check your fit before you apply.</p></div>', unsafe_allow_html=True)
    with st.form("new_job"):
        form_left, form_middle, form_right = st.columns([1.2, 1, 1])
        title = form_left.text_input("Role title")
        company = form_middle.text_input("Company")
        location = form_right.text_input("Location")
        description = st.text_area("Description", height=110)
        if st.form_submit_button("Add role", type="primary") and title and company and len(description) >= 20:
            add_job(title, company, location, description)
            st.success("Job added")
    if not jobs:
        st.markdown('<div class="empty-state">Your job library is ready for its first opportunity.</div>', unsafe_allow_html=True)
    for job in jobs:
        with st.expander(f"{job['title']}  /  {job['company']}  /  {job['location'] or 'Location not specified'}"):
            st.caption("Role description")
            st.write(job["description"])
            if resume_text:
                result = match_candidate(resume_text, job["description"])
                st.metric("Your fit", f"{result['score']}%", f"{len(result['matching_skills'])} skills aligned")
            if st.button("Track application", key=f"track-{job['id']}"):
                add_application(job["id"])
                st.success("Application saved")

with finder_tab:
    st.markdown('<div class="section-heading"><div class="eyebrow">03 / Job discovery</div><h2>Find your next opportunity</h2><p>Search trusted job platforms with one focused query, then save the roles worth pursuing.</p></div>', unsafe_allow_html=True)
    search_left, search_right = st.columns([1.4, 1])
    search_role = search_left.text_input("Role or skills", placeholder="e.g. Python developer, product designer")
    search_location = search_right.text_input("Location", placeholder="e.g. Remote, New York")
    if search_role:
        query = quote_plus(search_role.strip())
        location = quote_plus(search_location.strip() or "Remote")
        platform_columns = st.columns(3)
        for index, (platform, description, template) in enumerate(JOB_PLATFORMS):
            link = template.format(query=query, location=location)
            platform_columns[index % 3].markdown(
                f'<div class="platform-card"><h3>{platform}</h3><p>{description}</p><a class="platform-link" href="{link}" target="_blank">Search {platform} &rarr;</a></div>',
                unsafe_allow_html=True,
            )
        st.markdown("#### Saved roles matching your search")
        search_terms = search_role.lower().split()
        matching_jobs = [
            job for job in jobs
            if all(term in f"{job['title']} {job['company']} {job['location']} {job['description']}".lower() for term in search_terms)
            and (not search_location or search_location.lower() in f"{job['location']} {job['description']}".lower())
        ]
        if matching_jobs:
            for job in matching_jobs:
                with st.container(border=True):
                    job_left, job_right = st.columns([3, 1])
                    job_left.markdown(f"**{job['title']}**  \n{job['company']} · {job['location'] or 'Location not specified'}")
                    job_left.caption(job["description"][:180] + ("..." if len(job["description"]) > 180 else ""))
                    if resume_text:
                        result = match_candidate(resume_text, job["description"])
                        job_right.metric("Your fit", f"{result['score']}%")
                    if job_right.button("Track", key=f"find-track-{job['id']}"):
                        add_application(job["id"])
                        st.success(f"{job['title']} added to your tracker")
        else:
            st.markdown('<div class="empty-state">No saved roles match this search yet. Search the platforms above, then add promising roles to your Job library.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">Enter a role or skill above to search Google Jobs, LinkedIn, Indeed, Wellfound, Glassdoor, and Remote OK.</div>', unsafe_allow_html=True)

with tracker_tab:
    st.markdown('<div class="section-heading"><div class="eyebrow">04 / Application tracker</div><h2>Keep momentum visible</h2><p>A lightweight record of the roles you have decided to pursue.</p></div>', unsafe_allow_html=True)
    if applications:
        st.dataframe(applications, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="empty-state">No applications tracked yet. Start with a role from your job library.</div>', unsafe_allow_html=True)

with about_tab:
    st.markdown('<div class="section-heading"><div class="eyebrow">05 / About TalentLens</div><h2>A clearer way to make career decisions</h2><p>TalentLens turns a noisy job search into a focused, explainable workflow.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="about-band"><div class="eyebrow">Built for signal, not hype</div><h3>Your experience should be easier to understand.</h3><p>TalentLens helps you compare your real experience with the language employers use, so every application starts with context and a practical next step.</p></div>', unsafe_allow_html=True)
    st.markdown("#### How it works")
    step_columns = st.columns(3)
    for column, number, title, description in zip(
        step_columns,
        ["01", "02", "03"],
        ["Build your profile", "Understand your fit", "Track your momentum"],
        [
            "Upload a resume or paste your experience. TalentLens identifies the skills already in your background.",
            "Compare your profile with a role using semantic similarity and transparent skill coverage.",
            "Save roles and applications in one calm workspace so the next action is always visible.",
        ],
    ):
        column.markdown(f'<div class="about-card"><div class="step-number">{number}</div><h3>{title}</h3><p>{description}</p></div>', unsafe_allow_html=True)
    st.markdown("#### What makes it different")
    feature_columns = st.columns(3)
    for column, title, description in zip(
        feature_columns,
        ["Explainable by design", "Local-first privacy", "Useful next steps"],
        [
            "Every match shows the score, aligned skills, and gaps behind the recommendation.",
            "Your local workspace keeps profile and job data close to you during development.",
            "The goal is not a mysterious score. It is knowing what to improve or where to apply next.",
        ],
    ):
        column.markdown(f'<div class="about-card"><h3>{title}</h3><p>{description}</p></div>', unsafe_allow_html=True)
    st.markdown("#### Company and support")
    contact_columns = st.columns(4)
    for column, title, detail in zip(
        contact_columns,
        ["Visit us", "Call us", "Email us", "Support hours"],
        [COMPANY["address"], COMPANY["phone"], COMPANY["email"], COMPANY["hours"]],
    ):
        column.markdown(f'<div class="contact-card"><strong>{title}</strong><span>{detail}</span></div>', unsafe_allow_html=True)
    st.markdown("#### Send a support request")
    with st.form("support_request"):
        support_name, support_email = st.columns(2)
        name = support_name.text_input("Your name")
        email = support_email.text_input("Email address")
        message = st.text_area("How can we help?", height=100)
        if st.form_submit_button("Send request", type="primary"):
            if name and email and message:
                st.success(f"Thanks, {name}. Your request is ready to send to {COMPANY['email']}.")
            else:
                st.warning("Please add your name, email, and message before sending.")
    st.caption("TalentLens is an independent career intelligence workspace. Matching is deterministic and intended to support, not replace, your judgment.")

with assistant_tab:
    st.markdown('<div class="section-heading"><div class="eyebrow">06 / Customer care</div><h2>Ask the TalentLens assistant</h2><p>Get quick answers about the product, your workspace, and support.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-note">This local assistant answers common product questions without sending your resume or customer message to an external AI service.</div>', unsafe_allow_html=True)
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = [
            {"role": "assistant", "content": "Welcome to TalentLens support. Ask me about matching, resumes, privacy, saved roles, or contacting the company."}
        ]
    for message in st.session_state.assistant_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    prompt = st.chat_input("Ask about TalentLens...")
    if prompt:
        st.session_state.assistant_messages.append({"role": "user", "content": prompt})
        st.session_state.assistant_messages.append({"role": "assistant", "content": assistant_reply(prompt)})
        st.rerun()
