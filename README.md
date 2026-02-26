# CodeSphere v3

A comprehensive coding practice platform with AI-powered code quality analysis using Google Gemini API.

## Features

- **Problem Solving**: Solve coding problems with real-time test case validation
- **Code Quality Analysis**: Get AI-powered feedback on code quality, readability, maintainability, and efficiency
- **Performance Metrics**: Track execution time, test cases passed, and accuracy
- **Coding Habits**: Receive personalized suggestions to improve your coding habits
- **Admin Panel**: Add problems and manage test cases
- **User Dashboard**: Track your progress, submissions, and quality scores

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **AI Analysis**: Google Gemini API
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Authentication**: Flask-Login

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- MySQL Server
- MySQL user with CREATE DATABASE permission

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/codesphere_db
GEMINI_API_KEY=your-gemini-api-key-here
```

**Getting Gemini API Key:**
1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key
3. Add it to your `.env` file

**MySQL Setup:**
- Replace `username` and `password` with your MySQL credentials
- Replace `codesphere_db` with your desired database name
- The database will be created automatically on first run

### 4. Run the Application

```bash
python app.py
```

The application will:
- Create all database tables automatically
- Create a default admin user:
  - Email: `admin@codesphere.com`
  - Password: `admin123`

### 5. Access the Application

- Open your browser and go to: `http://localhost:5000`
- Login with the admin credentials or create a new account

## Usage

### For Users

1. **Register/Login**: Create an account or login
2. **Browse Problems**: Go to Problems page to see all available problems
3. **Solve Problems**: Click on a problem to open the code editor
4. **Submit Code**: Write your solution and click Submit
5. **View Results**: See test case results, execution time, and AI-generated quality report
6. **Track Progress**: Check your dashboard for statistics and recent submissions

### For Admins

1. **Login**: Use admin credentials to access admin dashboard
2. **Add Problems**: 
   - Go to Admin Dashboard
   - Click "Add New Problem"
   - Fill in problem details
3. **Add Test Cases**:
   - After creating a problem, you'll be redirected to add test cases
   - Add multiple test cases (visible or hidden)
   - Test cases are used to validate user submissions

## Project Structure

```
CodeSphere v3/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create this)
├── .env.example                   # Environment variables template
├── templates/
│   ├── index.html                 # Landing page
│   ├── login.html                 # Login/Register page
│   ├── userdashboard.html         # User dashboard
│   ├── problemLibrary.html        # Problem list
│   ├── problemsolver.html         # Code editor & results
│   ├── admindashboard.html        # Admin dashboard
│   ├── addnewproblem.html         # Add problem form
│   └── adminmanagetestcases.html  # Test case manager
└── README.md                      # This file
```

## Database Models

- **User**: User accounts and authentication
- **Problem**: Coding problems with descriptions
- **TestCase**: Input/output pairs for validation
- **Submission**: User code submissions with results
- **CodeQualityReport**: AI-generated quality analysis

## Code Execution

- Currently supports **Python only**
- Code is executed locally with a 5-second timeout
- Security measures include timeout limits and error handling
- Future: Docker-based execution for better security

## AI Code Quality Analysis

The Gemini API analyzes:
- **Overall Score**: Overall code quality (0-100)
- **Readability**: Code clarity and naming conventions
- **Maintainability**: Code structure and modularity
- **Efficiency**: Algorithm optimization
- **Best Practices**: Language-specific best practices
- **Complexity**: Time and space complexity analysis
- **Suggestions**: Actionable improvement suggestions
- **Coding Habits**: Personalized habit recommendations

## Security Notes

- Passwords are hashed using Werkzeug
- Code execution has timeout limits
- SQL injection protection via SQLAlchemy
- Session management via Flask-Login
- **Important**: For production, use Docker for code execution and add more security measures

## Troubleshooting

### Database Connection Error
- Check MySQL is running
- Verify credentials in `.env`
- Ensure database user has CREATE DATABASE permission

### Gemini API Not Working
- Verify API key in `.env`
- Check internet connection
- Application will use fallback values if API fails

### Code Execution Errors
- Ensure Python is installed and in PATH
- Check code syntax before submission
- Review error messages in results

## Future Enhancements

- Support for C++ and Java
- Docker-based code execution
- Real-time code editor (CodeMirror/Monaco)
- User rankings and leaderboards
- Problem difficulty ratings
- Code sharing and discussions

## License

This project is for educational purposes.

## Support

For issues or questions, please check the code comments or create an issue in the repository.

