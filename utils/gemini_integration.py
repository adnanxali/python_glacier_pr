import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel(Config.GEMINI_MODEL)

def get_risk_solution(growth_percentage, risk_binary, risk_level, area1, area2, growth_status):
    prompt = f"""
You are an environmental expert specializing in glacier monitoring and climate change analysis.

Glacier Analysis Results:
- Initial Glacier Area: {area1} pixels
- Current Glacier Area: {area2} pixels
- Growth Percentage: {growth_percentage:.2f}%
- Growth Status: {growth_status}
- AI Risk Assessment (Binary): {risk_binary}
- Risk Level: {risk_level}

Based on this glacier growth analysis, provide:
1. A brief explanation of what this growth pattern indicates
2. Specific environmental implications
3. 3-5 actionable recommendations to mitigate risks or monitor the situation
4. Any immediate safety concerns if applicable

Keep the response concise, professional, and actionable. Format it in clear sections.
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Unable to generate solution at this moment. Error: {str(e)}"