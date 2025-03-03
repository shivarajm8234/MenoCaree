from flask import Blueprint, render_template, request, jsonify, send_file
import os
from groq import Groq
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import uuid
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)

period_health = Blueprint('period_health', __name__)

# Initialize Groq client
try:
    groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    logging.info("Groq client initialized successfully in period_health.py")
except Exception as e:
    logging.error("Failed to initialize Groq client in period_health.py: %s", str(e))
    groq_client = None

# Load environment variables
load_dotenv()

# Groq client initialization moved to top of file

def generate_pdf_report(analysis_text, report_data):
    try:
        logging.info("Generating PDF report...")
        report_id = f"MC-{str(uuid.uuid4())[:8].upper()}"
        filename = f"report_{report_id}.pdf"
        current_date = datetime.now()
        
        # Get patient information
        patient_id = report_data.get('patientId', 'Not provided')
        patient_name = report_data.get('patientName', 'Not provided')
        age = report_data.get('age', 'Not provided')
        last_period = report_data.get('lastPeriod', 'Not provided')
        
        # Format the symptoms and conditions
        symptoms = report_data.get('symptoms', [])
        medical_conditions = report_data.get('medicalConditions', [])
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c5282')
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#2c5282')
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12
        )
        
        # Add title
        story.append(Paragraph('Professional Health Assessment Report', title_style))
        story.append(Spacer(1, 20))
        
        # Add report metadata
        story.append(Paragraph(f'Report ID: {report_id}', body_style))
        story.append(Paragraph(f'Generated on: {current_date.strftime("%Y-%m-%d %H:%M:%S")}', body_style))
        story.append(Spacer(1, 20))
        
        # Add patient information
        story.append(Paragraph('Patient Information', heading_style))
        patient_data = [
            ['Patient ID:', patient_id],
            ['Patient Name:', patient_name],
            ['Age:', age],
            ['Last Menstrual Period:', last_period]
        ]
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c5282')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        # Add symptoms
        if symptoms:
            story.append(Paragraph('Reported Symptoms', heading_style))
            for symptom in symptoms:
                story.append(Paragraph(f'• {symptom}', body_style))
            story.append(Spacer(1, 20))
        
        # Add medical conditions
        if medical_conditions:
            story.append(Paragraph('Medical Conditions', heading_style))
            for condition in medical_conditions:
                story.append(Paragraph(f'• {condition}', body_style))
            story.append(Spacer(1, 20))
        
        # Add analysis
        story.append(Paragraph('Health Analysis', heading_style))
        story.append(Paragraph(analysis_text, body_style))
        story.append(Spacer(1, 20))
        
        # Add disclaimer
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#c53030'),
            backColor=colors.HexColor('#fff5f5'),
            borderColor=colors.HexColor('#feb2b2'),
            borderWidth=1,
            borderPadding=10
        )
        story.append(Paragraph(
            'DISCLAIMER: This report is generated based on the information provided and should not be considered as a substitute for professional medical advice. Please consult with healthcare professionals for medical decisions.',
            disclaimer_style
        ))
        
        # Build PDF
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        
        logging.info("PDF report generated successfully")
        return pdf, filename
        
    except Exception as e:
        logging.error(f"Error in generate_pdf_report: {str(e)}")
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
        if not groq_client:
            logging.error("Groq client not initialized")
            return jsonify({
                'success': False,
                'error': "Groq client not initialized. Please check your environment variables and logs."
            }), 500

        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': "No data provided"
            }), 400

        # Extract data fields
        patient_id = data.get('patientId')
        patient_name = data.get('patientName')
        age = data.get('age')
        last_period = data.get('lastPeriod')
        symptoms = data.get('symptoms', [])
        medical_conditions = data.get('medicalConditions', [])

        # Prepare prompt for AI analysis
        prompt = f'''Analyze the following menstrual health information and provide a professional assessment:

Patient Information:
- Age: {age}
- Last Menstrual Period: {last_period}

Reported Symptoms:
{', '.join(symptoms) if symptoms else 'None reported'}

Medical Conditions:
{', '.join(medical_conditions) if medical_conditions else 'None reported'}

Provide a comprehensive analysis including:
1. Assessment of menstrual cycle regularity
2. Evaluation of reported symptoms
3. Potential correlations with medical conditions
4. General health recommendations
5. Any potential red flags that should be discussed with a healthcare provider

Please format the response in clear paragraphs.'''

        try:
            # Get AI analysis
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{
                    "role": "system",
                    "content": "You are a professional healthcare analyst specializing in menstrual health. Provide clear, professional analysis while being mindful of medical ethics and the importance of consulting healthcare providers."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.5,
                max_tokens=2048,
                top_p=1,
                stream=False
            )
            
            analysis_text = completion.choices[0].message.content
            
            # Generate PDF report
            report_data = {
                'patientId': patient_id,
                'patientName': patient_name,
                'age': age,
                'lastPeriod': last_period,
                'symptoms': symptoms,
                'medicalConditions': medical_conditions
            }
            
            pdf_content, filename = generate_pdf_report(analysis_text, report_data)
            
            # Save PDF to temporary file
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, filename)
            
            with open(temp_path, 'wb') as f:
                f.write(pdf_content)
            
            return jsonify({
                'success': True,
                'analysis': analysis_text,
                'filename': filename
            })
            
        except Exception as ai_error:
            logging.error("AI analysis error: %s", str(ai_error))
            return jsonify({
                'success': False,
                'error': "Failed to generate AI analysis"
            }), 500
            
    except Exception as e:
        logging.error("Error in analyze_report: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


























    try:
        # Verify Groq client is initialized
        if not groq_client:
            logging.error("Groq client not initialized")
            return jsonify({
                'success': False,
                'error': "Groq client not initialized. Please check your environment variables and logs."
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
        if not groq_client:
            logging.error("Groq client not initialized")
            return jsonify({
                'success': False,
                'error': "Groq client not initialized. Please check your environment variables and logs."
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
