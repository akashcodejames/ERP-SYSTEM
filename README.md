1. Git clone <repository-url>
```
   cd <repository-name>
```

2. Create and activate a Python virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install flask flask-sqlalchemy flask-login flask-migrate python-dotenv email-validator werkzeug gunicorn mysql-connector-python pymysql
   ```

4. Database Setup:

   ### For SQLite (Default - No additional setup required):
   - The application will automatically create an `app.db` file in your project directory
   - No configuration needed in `.env` file

   ### For MySQL:
   1. Create a MySQL database:
      ```sql
      CREATE DATABASE your_database_name;
      ```
   2. Create a `.env` file from the template:
      ```bash
      cp .env .env
      ```
   3. Edit `.env` and configure your MySQL connection:
      ```
      FLASK_SECRET_KEY=your_secret_key_here
      FLASK_DEBUG=True
      DATABASE_URL=mysql://username:password@localhost:3306/your_database_name
      ```

5. Run the application:
   ```bash
   python main.py