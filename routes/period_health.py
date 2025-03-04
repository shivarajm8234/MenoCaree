from flask import Blueprint, render_template, request, jsonify, send_file
import os
from groq import Groq
from dotenv import load_dotenv
import pdfkit
import io
import uuid
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)

period_health = Blueprint('period_health', __name__)

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_api_key = os.getenv('GROQ_API_KEY')
logging.debug("GROQ_API_KEY found: %s", bool(groq_api_key))

if not groq_api_key:
    logging.error("GROQ_API_KEY environment variable is not set")
    raise ValueError("GROQ_API_KEY environment variable is not set")

try:
    groq_client = Groq(
        api_key=groq_api_key
    )
    logging.info("Groq client initialized successfully")
except Exception as e:
    logging.error("Failed to initialize Groq client: %s", str(e))
    raise

def generate_pdf_report(analysis_text, report_data):
    try:
        logging.info("Generating PDF report...")
        report_id = f"MC-{str(uuid.uuid4())[:8].upper()}"
        current_date = datetime.now()
        
        # Get patient information
        patient_id = report_data.get('patientId', 'Not provided')
        patient_name = report_data.get('patientName', 'Not provided')
        
        # Format the symptoms and conditions
        symptoms = report_data.get('symptoms', [])
        medical_conditions = report_data.get('medicalConditions', [])
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>MenoCare Professional Health Report</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #2c5282 0%, #1a365d 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    margin-bottom: 30px;
                }}
                .patient-info {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 15px;
                }}
                .report-info {{
                    background: #f8fafc;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border: 1px solid #e2e8f0;
                }}
                .section {{
                    background: white;
                    padding: 25px;
                    margin: 20px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    font-size: 28px;
                    margin: 0;
                    padding-bottom: 10px;
                    border-bottom: 2px solid rgba(255, 255, 255, 0.3);
                }}
                h2 {{
                    color: #2c5282;
                    font-size: 22px;
                    margin-top: 0;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #e2e8f0;
                }}
                .meta-info {{
                    color: rgba(255, 255, 255, 0.9);
                    margin-top: 10px;
                    font-size: 14px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e2e8f0;
                }}
                th {{
                    background-color: #f8fafc;
                    color: #2c5282;
                    font-weight: 600;
                }}
                ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                li {{
                    margin: 8px 0;
                    line-height: 1.5;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid #e2e8f0;
                    color: #666;
                    font-size: 14px;
                }}
                .disclaimer {{
                    background: #fff5f5;
                    border: 1px solid #feb2b2;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #c53030;
                }}
                .logo {{
                    text-align: right;
                    margin-bottom: 10px;
                }}
                .watermark {{
                    position: fixed;
                    bottom: 0;
                    right: 0;
                    opacity: 0.1;
                    z-index: -1;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Professional Health Assessment Report</h1>
                    <div class="meta-info">
                        <p>Report ID: {report_id}</p>
                        <p>Generated on: {current_date.strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                    <div class="patient-info">
                        <p><strong>Patient ID:</strong> {patient_id}</p>
                        <p><strong>Patient Name:</strong> {patient_name}</p>
                    </div>
                </div>

                <div class="report-info">
                    <h2>Patient Information</h2>
                    <table>
                        <tr>
                            <th>Category</th>
                            <th>Details</th>
                        </tr>
                        <tr>
                            <td>Age</td>
                            <td>{report_data.get('age', 'Not provided')}</td>
                        </tr>
                        <tr>
                            <td>Last Menstrual Period</td>
                            <td>{report_data.get('lastPeriodDate', 'Not provided')}</td>
                        </tr>
                        <tr>
                            <td>Cycle Length</td>
                            <td>{report_data.get('cycleLength', 'Not provided')}</td>
                        </tr>
                        <tr>
                            <td>Flow Intensity</td>
                            <td>{report_data.get('flowIntensity', 'Not provided')}</td>
                        </tr>
                        <tr>
                            <td>Cycle Regularity</td>
                            <td>{report_data.get('cycleRegularity', 'Not provided')}</td>
                        </tr>
                    </table>
                </div>

                <div class="section">
                    <h2>Reported Symptoms</h2>
                    <table>
                        <tr>
                            <th>Symptom</th>
                        </tr>
                        {''.join(f'<tr><td>{symptom}</td></tr>' for symptom in symptoms) if symptoms else '<tr><td>No symptoms reported</td></tr>'}
                    </table>
                </div>

                <div class="section">
                    <h2>Medical History</h2>
                    <table>
                        <tr>
                            <th>Condition</th>
                        </tr>
                        {''.join(f'<tr><td>{condition}</td></tr>' for condition in medical_conditions) if medical_conditions else '<tr><td>No medical conditions reported</td></tr>'}
                    </table>
                </div>

                <div class="section">
                    <h2>Professional Analysis</h2>
                    {analysis_text.replace('\n', '<br>')}
                </div>

                <div class="disclaimer">
                    <strong>Medical Disclaimer:</strong>
                    <p>This report is generated based on the information provided and should be used for informational purposes only. It is not intended to be a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.</p>
                </div>

                <div class="footer">
                    <p>MenoCare Professional Health Report</p>
                    <p>Report ID: {report_id} | Generated: {current_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p> {current_date.year} MenoCare. All rights reserved.</p>
                </div>

                <div class="watermark">
                    MenoCare Report {report_id} | {current_date.strftime('%Y-%m-%d')}
                </div>
            </div>
        </body>
        </html>
        """

        # Configure pdfkit options
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None,
            'footer-right': f'[page] of [topage]',
            'footer-font-size': '8',
            'header-font-size': '8',
            'header-right': f'Report ID: {report_id}',
            'header-spacing': '5'
        }

        # Generate PDF
        try:
            pdf = pdfkit.from_string(html_content, False, options=options)
            filename = f"MenoCare_Professional_Report_{current_date.strftime('%Y%m%d')}_{report_id}.pdf"
            logging.info("PDF report generated successfully")
            return pdf, filename
        except Exception as pdf_error:
            logging.error("PDF generation error: %s", str(pdf_error))
            raise Exception("Failed to generate PDF report") from pdf_error

    except Exception as e:
        logging.error("Error in generate_pdf_report: %s", str(e))
        raise

@period_health.route('/health_report')
def health_report():
    try:
        return render_template('health_report.html')
    except Exception as e:
        logging.error("Error rendering health report template: %s", str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to load the health report page'
        }), 500

@period_health.route('/api/analyze_report', methods=['POST'])
def analyze_report():
    try:
        # Verify Groq client is initialized
        if not groq_api_key:
            logging.error("GROQ_API_KEY not found")
            return jsonify({
                'success': False,
                'error': "API key not configured. Please check your environment variables."
            }), 500

        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        logging.debug("Received data for analysis: %s", data)
        
        report_content = data.get('report_content', {})
        concerns = data.get('concerns', '')
        
        if not report_content:
            return jsonify({
                'success': False,
                'error': "No report content provided"
            }), 400

        # Format the data for analysis
        symptoms = report_content.get('symptoms', [])
        symptom_text = "\n".join(f"- {symptom}" for symptom in symptoms) if symptoms else "No symptoms reported"
        
        medical_conditions = report_content.get('medicalConditions', [])
        conditions_text = "\n".join(f"- {condition}" for condition in medical_conditions) if medical_conditions else "No medical conditions reported"
        
        notes_text = concerns.strip() if concerns else "No additional notes provided"
        
        prompt = f"""As a professional healthcare AI assistant specializing in menopause and women's health, please provide a comprehensive analysis of this patient's health data:

        PATIENT PROFILE:
        Age: {report_content.get('age', 'Not provided')}
        Last Menstrual Period: {report_content.get('lastPeriodDate', 'Not provided')}
        Cycle Length: {report_content.get('cycleLength', 'Not provided')}
        Flow Intensity: {report_content.get('flowIntensity', 'Not provided')}
        Cycle Regularity: {report_content.get('cycleRegularity', 'Not provided')}

        REPORTED SYMPTOMS:
        {symptom_text}

        MEDICAL HISTORY:
        {conditions_text}

        ADDITIONAL NOTES:
        {notes_text}

        Please provide a detailed, evidence-based analysis in the following format. Use clear, professional medical terminology while ensuring the information is accessible to patients:

        1. CURRENT HEALTH ASSESSMENT
        - Comprehensive analysis of reported symptoms and their clinical significance
        - Evaluation of menstrual cycle patterns and implications
        - Impact of existing medical conditions on current health status
        - Overall health status evaluation

        2. RISK ASSESSMENT
        - Identified risk factors based on symptoms and medical history
        - Potential health implications if not addressed
        - Critical areas requiring immediate attention
        - Long-term health considerations

        3. CLINICAL RECOMMENDATIONS
        - Evidence-based management strategies
        - Lifestyle modifications with specific, actionable steps
        - Dietary recommendations with scientific rationale
        - Exercise and physical activity guidelines
        - Stress management techniques

        4. MEDICAL GUIDANCE
        - Specific symptoms requiring immediate medical attention
        - Recommended medical screenings and their frequency
        - Important questions to discuss with healthcare providers
        - Monitoring and tracking recommendations

        5. SUPPORT AND RESOURCES
        - Recommended support groups and communities
        - Educational resources for further information
        - Self-care strategies and their benefits
        - Professional care options and when to seek them

        Important: Base all recommendations on current medical evidence and best practices. Avoid speculative statements. If certain information is insufficient for a complete assessment, note this clearly.

        Format each section with clear headings and bullet points. Focus on actionable insights while maintaining professional medical accuracy."""
        
        logging.info("Calling Groq API for analysis...")
        try:
            response = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {
                        "role": "system",
                        "content": "You are MenoCare, a medical AI assistant specializing in menopause and women's health. Provide clear, professional advice formatted with headings and bullet points."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=1,
                stream=False
            )

            analysis_text = response.choices[0].message.content
            logging.debug("Received API response")
            
            # Generate PDF report
            try:
                pdf_content, filename = generate_pdf_report(analysis_text, report_content)
                
                return jsonify({
                    'success': True,
                    'analysis': analysis_text,
                    'pdf': {
                        'content': pdf_content.hex(),
                        'filename': filename
                    }
                })
            except Exception as pdf_error:
                logging.error("PDF generation error: %s", str(pdf_error))
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate PDF report'
                }), 500

        except Exception as api_error:
            logging.error("API error: %s", str(api_error))
            return jsonify({
                'success': False,
                'error': 'Failed to analyze the report'
            }), 500

    except Exception as e:
        logging.error("Server error: %s", str(e))
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500

@period_health.route('/api/download_report', methods=['POST'])
def download_report():
    try:
        data = request.get_json()
        if not data or 'content' not in data or 'filename' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid request data'
            }), 400

        content = bytes.fromhex(data['content'])
        filename = data['filename']
        
        return send_file(
            io.BytesIO(content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logging.error("Error downloading report: %s", str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to download report'
        }), 500

@period_health.route('/api/download_report/<filename>')
def download_report_get(filename):
    try:
        # Get the PDF content from the session or regenerate it
        pdf_content = request.args.get('content')
        if not pdf_content:
            return "PDF content not found", 404
        
        # Convert hex back to bytes
        pdf_bytes = bytes.fromhex(pdf_content)
        
        # Create BytesIO object
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logging.error("Error downloading report: %s", str(e))
        return jsonify({'error': str(e)}), 500

@period_health.route('/api/analyze-symptoms', methods=['POST'])
def analyze_symptoms():
    try:
        # Verify Groq client is initialized
        if not groq_api_key:
            logging.error("GROQ_API_KEY not found")
            return jsonify({
                'success': False,
                'error': "API key not configured. Please check your environment variables."
            }), 500

        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': "No data provided"
            }), 400
            
        logging.debug("Received data for analysis: %s", data)
        
        symptoms = data.get('symptoms', [])
        notes = data.get('notes', '')
        
        if not symptoms:
            return jsonify({
                'success': False,
                'error': "No symptoms provided"
            }), 400
        
        # Format symptoms for the prompt
        symptom_details = []
        for symptom in symptoms:
            name = symptom.get('name', '').strip()
            severity = symptom.get('severity', 5)
            if name:
                symptom_details.append(f"- {name} (Severity: {severity}/10)")
        
        symptom_text = "\n".join(symptom_details) if symptom_details else "No specific symptoms reported"
        notes_text = notes.strip() if notes else "No additional notes provided"
        
        prompt = f"""
        Please analyze these menopause symptoms and provide a comprehensive analysis:

        Symptoms:
        {symptom_text}

        Additional Notes:
        {notes_text}

        Please provide a detailed analysis in the following format:

        1. Current Symptoms Analysis
        - Detailed analysis of each reported symptom
        - Potential underlying causes
        - Severity assessment

        2. Future Health Implications
        - Potential progression
        - Related symptoms to watch for
        - Long-term considerations

        3. Prevention Strategies
        - Lifestyle modifications
        - Diet and exercise
        - Stress management

        4. Treatment Options
        - Immediate relief measures
        - Long-term management
        - Natural remedies

        5. When to Seek Medical Attention
        - Warning signs
        - Emergency symptoms
        - Recommended screenings

        6. Support and Resources
        - Support groups
        - Educational materials
        - Self-care strategies
        - Professional care options

        Format each section with clear headings and bullet points."""
        
        logging.info("Calling Groq API for analysis...")
        try:
            response = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {
                        "role": "system",
                        "content": "You are MenoCare, a medical AI assistant specializing in menopause care. Provide clear, professional advice formatted with headings and bullet points."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=1,
                stream=False
            )
            
            response_text = response.choices[0].message.content
            logging.debug("Received API response")
            
            # Parse the response into sections
            sections = {
                'current_symptoms_analysis': '',
                'future_health_implications': '',
                'prevention_strategies': '',
                'treatment_options': '',
                'when_to_seek_medical_attention': '',
                'support_and_resources': ''
            }
            
            current_section = None
            section_text = []
            
            for line in response_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                if '1. Current Symptoms Analysis' in line:
                    current_section = 'current_symptoms_analysis'
                    section_text = []
                elif '2. Future Health Implications' in line:
                    if current_section:
                        sections[current_section] = '\n'.join(section_text).strip()
                    current_section = 'future_health_implications'
                    section_text = []
                elif '3. Prevention Strategies' in line:
                    if current_section:
                        sections[current_section] = '\n'.join(section_text).strip()
                    current_section = 'prevention_strategies'
                    section_text = []
                elif '4. Treatment Options' in line:
                    if current_section:
                        sections[current_section] = '\n'.join(section_text).strip()
                    current_section = 'treatment_options'
                    section_text = []
                elif '5. When to Seek Medical Attention' in line:
                    if current_section:
                        sections[current_section] = '\n'.join(section_text).strip()
                    current_section = 'when_to_seek_medical_attention'
                    section_text = []
                elif '6. Support and Resources' in line:
                    if current_section:
                        sections[current_section] = '\n'.join(section_text).strip()
                    current_section = 'support_and_resources'
                    section_text = []
                elif current_section:
                    section_text.append(line)
            
            # Add the last section
            if current_section and section_text:
                sections[current_section] = '\n'.join(section_text).strip()
            
            # Add default message for empty sections
            for key in sections:
                if not sections[key]:
                    sections[key] = 'No specific information available for this section.'
            
            logging.debug("Analysis completed successfully")
            return jsonify({
                'success': True,
                'analysis': sections
            })
            
        except Exception as api_error:
            logging.error("API Error: %s", str(api_error))
            return jsonify({
                'success': False,
                'error': f"Failed to analyze symptoms: {str(api_error)}"
            }), 500
            
    except Exception as e:
        logging.error("Server Error: %s", str(e))
        return jsonify({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }), 500
