import streamlit as st
import pdfplumber
import docx
import google.generativeai as genai
import json


genai.configure(api_key="AIzaSyBhhFqcwH1EDdX6E1Nlfz6imtzjoYyX9Sg")  

def read_resume(file):
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return file.read().decode("utf-8")

def extract_info_with_gemini(resume_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
Extract the following details from this resume and return them as a valid JSON object. 
Do NOT add any explanation or markdown formatting. Only return a valid JSON.

Required fields:
- Name
- Email
- Phone
- Skills
- Education
- Work Experience

Example format:
{{
  "Name": "John Doe",
  "Email": "john.doe@example.com",
  "Phone": "+91-9876543210",
  "Skills": ["Python", "Java", "SQL"],
  "Education": ["B.Tech in Computer Science - XYZ University"],
  "Work Experience": ["Software Engineer at ABC Corp (2020-2023)", "Intern at DEF Ltd (2019-2020)"]
}}

Resume:
{resume_text}
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def suggest_jobs(skills):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
Suggest job roles for a candidate with the following skills: {skills}.
Only list job titles (no companies or descriptions). Limit to 5-7 roles.
Output each title on a new line.
Prioritize job roles according to the skills (for example if the skills belong to backend web development then suggest jobs based on backend web  development only)
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def parse_skills_from_json(parsed_json):
    try:
        if isinstance(parsed_json, str):
            # Strip Markdown code fences if present
            parsed_json = parsed_json.strip()
            if parsed_json.startswith("```"):
                parsed_json = "\n".join(parsed_json.splitlines()[1:-1])
            
            parsed_json = json.loads(parsed_json)
        
        return parsed_json.get("Skills", "")
    
    except Exception as e:
        print("❌ Error parsing skills:", e)
        return ""


st.title("📄 Resume Parser")

uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx", "txt"])

if uploaded_file:
    resume_text = read_resume(uploaded_file)
    st.subheader("📃 Resume Text")
    st.text_area("Raw Resume Text", resume_text, height=300)

    if st.button("✨ Parse Resume and Suggest Jobs"):
        with st.spinner("🔍 Parsing your resume..."):
            parsed_resume = extract_info_with_gemini(resume_text)

           
            st.subheader("🔍Raw Output")
            st.text(parsed_resume)

            
            skills = parse_skills_from_json(parsed_resume)
            print(skills)


            skills_str = ", ".join(skills) if isinstance(skills, list) else skills

            job_roles = suggest_jobs(skills_str)

        st.subheader("💼 Job Roles You Can Apply For")

        
        st.markdown("""
    <style>
    .tile-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
        padding: 15px 0;
    }

    .job-tile {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        padding: 18px 22px;
        color: white;
        font-weight: 600;
        font-size: 1rem;
        text-align: center;
        min-width: 200px;
        max-width: 250px;
        transition: all 0.3s ease;
    }

    .job-tile:hover {
        transform: scale(1.04);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
        background: rgba(255, 255, 255, 0.25);
        cursor: pointer;
    }

    @media (max-width: 600px) {
        .job-tile {
            min-width: 100%;
            font-size: 0.95rem;
            padding: 14px 16px;
        }
    }
    </style>
""", unsafe_allow_html=True)

        
        job_list = job_roles.splitlines()
        tile_html = '<div class="tile-container">' + "".join(
            [f'<div class="job-tile">{role}</div>' for role in job_list]
        ) + '</div>'

        st.markdown(tile_html, unsafe_allow_html=True)



        combined_output = {
            "parsed_resume": parsed_resume,
            "suggested_jobs": job_roles.splitlines()
        }

        export_text = json.dumps(combined_output, indent=2)

        st.download_button(
            label="📥 Download Results as JSON",
            data=export_text,
            file_name="resume_parsed_and_jobs.json",
            mime="application/json"
        )
