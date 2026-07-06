import re

path = r'd:\ai-doctor-v3\frontend\components\frontend_EnhancedMedicalChat.jsx'
text = open(path, encoding='utf-8').read()

if 'apiFetch' not in text:
    # Replace fetch( with apiFetch( except window.fetch
    text = re.sub(r'(?<!\.)\bfetch\(', 'apiFetch(', text)
    
    api_fetch_code = """
const apiFetch = async (url, options = {}) => {
  const token = localStorage.getItem("ai_doctor_token");
  const headers = { ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  
  const res = await window.fetch(url, { ...options, headers });
  if (res.status === 401 || res.status === 403) {
    window.dispatchEvent(new Event("auth_error"));
  }
  return res;
};
"""
    text = text.replace('const API = process.env.NEXT_PUBLIC_API_URL ||', api_fetch_code + '\nconst API = process.env.NEXT_PUBLIC_API_URL ||')
    
    open(path, 'w', encoding='utf-8').write(text)
    print('Refactored fetch to apiFetch')
else:
    print('Already refactored')
