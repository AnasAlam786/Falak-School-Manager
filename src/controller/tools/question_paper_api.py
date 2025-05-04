# src/controller/tools/question_paper_api.py

from flask import session, render_template, redirect, url_for, request, jsonify, Blueprint
from bs4 import BeautifulSoup


question_paper_api_bp = Blueprint( 'question_paper_api_bp',   __name__)


@question_paper_api_bp.route('/question_paper_api', methods=["POST"])
def question_paper_api():
    if 'email' not in session:
        return jsonify({'message': "Not Authorised!"}), 400

       
    payload = request.json
    value =  payload.get('value')

    if value=="a4PDF":
        questions =  payload.get('questions')
        event =  payload.get('eventName')
        subject =  payload.get('subject')
        std =  payload.get('std')
        MM =  payload.get('MM')
        hrs =  payload.get('hrs')
        school="Falak Public School"

        #questions = [{"marks": "10", "type": "singleWord", "qText": "Define the following:", "subQuestion": ["India", "France", "Japan", "Germany", "Brazil", "Canada"]},
                    # {"marks": "10", "type": "match", "qText": "Match the following countries with their capitals:", "subQuestion": ["India", "France", "Japan", "Germany", "Brazil", "Canada"], "options": ["New Delhi", "Paris", "Tokyo", "Berlin", "Brasília", "Ottawa"]}, 
                    # {"type": "QnA","marks": "10",  "qText": "Answer the following general knowledge questions:", "subQuestion": ["Who is known as the Father of the Nation in India?", "What is the chemical symbol for water?", "Who wrote 'Pride and Prejudice'?", "What is the highest mountain in the world?", "Which planet is known as the Red Planet?"]}, 
                    # {"type": "fillUp", "qText": "Fill in the blanks:", "marks": "10", "subQuestion": ["The Great Wall of _____ is visible from space.", "The boiling point of water is _____ degrees Celsius.", "Albert Einstein developed the theory of _____", "The largest desert in the world is the _____ Desert.", "Light travels at approximately _____ km/s."]}, 
                    # {"type": "T-F", "marks": "10", "qText": "State whether the following statements are True or False:", "subQuestion": ["The Great Pyramid of Giza is one of the Seven Wonders of the Ancient World.", "The Pacific Ocean is the smallest ocean in the world.", "Mount Everest is in the Himalayas.", "Venus is the hottest planet in the solar system.", "The human body has 206 bones."]}, 
                    # {"type": "mcq", "qText": "Choose the correct options:", "marks": "10", "subQuestion": [{"text": "Which is the largest mammal on Earth?", "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"]}, 
                    # {"marks": "10", "text": "Which is the closest star to Earth?", "options": ["Proxima Centauri", "Sirius", "Betelgeuse", "Alpha Centauri"]}, {"text": "Which is the longest river in the world?", "options": ["Amazon", "Nile", "Yangtze", "Mississippi"]}, {"text": "Which of the following is a primary color?", "options": ["Red", "Green", "Blue", "Yellow"]}]}, 
                    # {"type": "mcq", "qText": "Science and Technology Questions:", "subQuestion": [{"text": "Who invented the light bulb?", "options": ["Thomas Edison", "Nikola Tesla", "Alexander Graham Bell", "Isaac Newton"]}, {"text": "Which planet has the most moons?", "options": ["Jupiter", "Saturn", "Mars", "Uranus"]}, {"text": "What does CPU stand for?", "options": ["Central Processing Unit", "Computer Power Unit", "Control Panel Unit", "Central Program Unit"]}, {"text": "What is the chemical formula for carbon dioxide?", "options": ["CO2", "H2O", "O2", "C2O"]}]}]

        html = render_template('paper_elements.html',questions=questions, school=school, event=event, subject=subject, std=std,MM=MM, hrs=hrs)
        soup=BeautifulSoup(html,"lxml")
        content = soup.find('div', id=value).decode_contents()

        paper_key = f"{subject}_{std}"

        if 'papers' not in session:
            session['papers'] = {}

        session["papers"][paper_key] = questions
        session.modified = True

        return jsonify({"html":str(content)})


    if isinstance(value, int):
        html = render_template('paper_elements.html',index=value)
        soup=BeautifulSoup(html,"lxml")
        content = soup.find('div', id="Question").decode_contents()
        
        return jsonify({"html":str(content)})

    html = render_template('paper_elements.html')
    soup=BeautifulSoup(html,"lxml")
    content = soup.find('div', id=value)
    
    return jsonify({"html":str(content)})
        
