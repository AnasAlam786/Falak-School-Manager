from src import create_app

app = create_app()

if __name__ == "__main__":
    # app.run(port=2000, debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)

    #app.run(debug=True)
    # To activate your virtual environment, run the following command in your terminal (not in this Python file):
    # On Windows:
    #   .\venv\Scripts\activate
    # On macOS/Linux:P
    #   source venv/bin/activateP