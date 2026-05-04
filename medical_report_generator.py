import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class MedicalReportGenerator:
    """
    Medical Report Generator with OpenAI GPT integration.

    FIX 3: Replaced deprecated openai v0.x API (openai.ChatCompletion.create)
            with the current openai v1+ client (openai.OpenAI / client.chat.completions.create).
    FIX 4: API key is read from .env — never hardcoded.
    FIX 5: Silent fallback is preserved but now logs the real error reason clearly.
    """

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.openai_available = False
        self.client = None

        if self.api_key and self.api_key.strip() not in ('', 'your_openai_api_key_here'):
            try:
                # FIX 3: Use the v1+ OpenAI client — works with openai>=1.0.0
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.openai_available = True
                print("✓ OpenAI API client initialized successfully")
            except ImportError:
                print("⚠️  openai package not installed. Run: pip install openai>=1.0.0")
            except Exception as e:
                print(f"⚠️  OpenAI client initialization failed: {e}")
        else:
            print("⚠️  OPENAI_API_KEY not set. Using template-based fallback reports.")
            print("   Set OPENAI_API_KEY in .env to enable GPT-powered reports.")

        # Cancer information database
        self.cancer_info = {
            'adenocarcinoma': {
                'description': 'Most common type of lung cancer, typically found in outer areas of lungs',
                'treatment': 'Surgery, chemotherapy (Cisplatin/Paclitaxel), targeted therapy, immunotherapy',
                'prognosis': 'Variable depending on stage; early detection improves outcomes significantly'
            },
            'large.cell.carcinoma': {
                'description': 'Aggressive form of non-small cell lung cancer with rapid growth',
                'treatment': 'Surgery, radiation therapy, chemotherapy (Carboplatin/Paclitaxel)',
                'prognosis': 'Requires aggressive treatment; early intervention is critical'
            },
            'squamous.cell.carcinoma': {
                'description': 'Typically develops in central airways, strongly linked to smoking',
                'treatment': 'Surgery, radiation therapy, chemotherapy (Cisplatin-based regimens)',
                'prognosis': 'Good response to treatment when detected early'
            },
            'normal': {
                'description': 'No malignant tissue detected in the analyzed CT scan',
                'treatment': 'Continue regular screening and maintain healthy lifestyle',
                'prognosis': 'Excellent; maintain preventive care and regular check-ups'
            }
        }

    def get_basic_recommendation(self, cancer_type):
        """Return treatment recommendation string for a given cancer type key."""
        return self.cancer_info.get(cancer_type, {}).get(
            'treatment', 'Consult oncologist for treatment plan'
        )

    def generate_medical_report(self, prediction, confidence, cancer_type):
        """
        Generate a comprehensive medical report.
        Uses GPT-3.5-turbo if OpenAI client is available, otherwise uses template fallback.

        Args:
            prediction  : Display name of predicted class  (e.g. 'Adenocarcinoma')
            confidence  : Float confidence score 0–1       (e.g. 0.837)
            cancer_type : Internal class key               (e.g. 'adenocarcinoma')

        Returns:
            str: Formatted medical report text
        """
        if self.openai_available and self.client is not None:
            try:
                return self._generate_gpt_report(prediction, confidence, cancer_type)
            except Exception as e:
                # Log the real error — do not silently swallow it
                print(f"⚠️  GPT report generation failed ({type(e).__name__}: {e})")
                print("   Falling back to template report.")

        return self._generate_fallback_report(prediction, confidence, cancer_type)

    def _generate_gpt_report(self, prediction, confidence, cancer_type):
        """
        Call OpenAI GPT-3.5-turbo using the v1+ client API.

        FIX 3 applied here: client.chat.completions.create() replaces
        the removed openai.ChatCompletion.create().
        """
        cancer_info = self.cancer_info.get(cancer_type, {})
        cancer_desc = cancer_info.get('description', 'Unknown cancer type')

        prompt = f"""Generate a professional medical report for a lung cancer CT scan analysis.

Prediction: {prediction}
Confidence Score: {confidence:.2%}
Cancer Type: {cancer_type.replace('.', ' ').title()}
Description: {cancer_desc}

Include these sections:
1. SUMMARY OF FINDINGS
2. AI CONFIDENCE ASSESSMENT
3. DETAILED CANCER TYPE INFORMATION
4. CLINICAL RECOMMENDATIONS
5. IMPORTANT DISCLAIMER

Keep it under 500 words. Use formal medical report formatting."""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a medical AI assistant generating formal radiology reports. "
                        "Be professional, accurate, and include appropriate disclaimers."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )

        return response.choices[0].message.content

    def _generate_fallback_report(self, prediction, confidence, cancer_type):
        """Template-based report used when OpenAI is unavailable."""
        cancer_info = self.cancer_info.get(cancer_type, {})
        cancer_desc = cancer_info.get('description', 'Unknown cancer type')
        basic_treatment = cancer_info.get('treatment', 'Consult oncologist')
        prognosis = cancer_info.get('prognosis', 'Consult healthcare provider')

        if confidence >= 0.90:
            confidence_level = "Very High"
            confidence_note = "The model shows very high confidence in this classification."
        elif confidence >= 0.75:
            confidence_level = "High"
            confidence_note = "The model shows high confidence in this classification."
        elif confidence >= 0.60:
            confidence_level = "Moderate"
            confidence_note = "The model shows moderate confidence. Additional review recommended."
        else:
            confidence_level = "Low"
            confidence_note = "The model shows low confidence. Further diagnostic testing strongly recommended."

        sep = '=' * 80
        report = f"""{sep}
LUNG CANCER CT SCAN ANALYSIS REPORT
{sep}

Report Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Method  : EfficientNet-B4 Deep Learning Model

{sep}
1. SUMMARY OF FINDINGS
{sep}

The AI analysis has identified the lung tissue as: {prediction}

Confidence Level : {confidence_level} ({confidence:.1%})
{confidence_note}

{sep}
2. AI CONFIDENCE ASSESSMENT
{sep}

Model Confidence Score : {confidence:.2%}
Classification Method  : Transfer Learning with EfficientNet-B4 Architecture
Training Dataset       : Clinical-grade lung CT scan images

{sep}
3. DETAILED CANCER TYPE INFORMATION
{sep}

Condition    : {prediction}
Description  : {cancer_desc}
Prognosis    : {prognosis}

{sep}
4. CLINICAL RECOMMENDATIONS
{sep}

Recommended Treatment : {basic_treatment}

Next Steps:
  - Immediate consultation with a board-certified oncologist
  - Additional diagnostic imaging (PET scan, MRI) as recommended
  - Biopsy for histological confirmation
  - Comprehensive staging workup
  - Multidisciplinary team discussion

{sep}
5. IMPORTANT DISCLAIMER
{sep}

⚠️  CRITICAL NOTICE:
This analysis is generated by an AI system for research and educational purposes only.
This report must NOT be used as a substitute for professional medical diagnosis.

  • AI predictions require validation by qualified healthcare professionals
  • Final diagnosis must be confirmed through standard clinical procedures
  • Treatment decisions must only be made by licensed medical practitioners

{sep}
Generated by : Enhanced Lung Cancer AI Classifier System
Model Version : EfficientNet-B4
Report ID     : {datetime.now().strftime('%Y%m%d%H%M%S')}
{sep}"""

        return report.strip()
