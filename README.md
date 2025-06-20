# Job Platform API

A RESTful API for companies to post job listings and applicants to browse and apply for jobs, built with Django and Django REST Framework.

** Setup Instructions**

1. Clone the Repository

         git clone https://github.com/YishakG/job_platform
         cd job_platform
3. Create a Virtual Environment

         python -m venv venv
   
         venv\Scripts\activate #on Mac use: source venv/bin/activate 
4. Create a Virtual Environment   

         pip install -r requirements.txt
6. Set Up Environment Variables
    Create a .env file in the project root with the  following:
   
       SECRET_KEY=your-secret-key
      
       DATABASE_URL=sqlite:///db.sqlite3
      
       CLOUDINARY_CLOUD_NAME=your-cloud-name
      
       CLOUDINARY_API_KEY=your-api-key
      
       CLOUDINARY_API_SECRET=your-api-secret
   
7. Run Migrations

       python manage.py makemigrations
   
       python manage.py migrate
9. Create a Superuser (Optional)

         python manage.py createsuperuser
11. Run the Server

          python manage.py runserver
   
12. Test the API
    Access the API at http://localhost:8000/api/.
    
    Use tools like Postman or curl to test endpoints.
    
    Example: Login with POST /api/token/ using email and password.

**Technology Choices**

      Django: Robust framework for rapid development and security.
      
      Django REST Framework: Simplifies building RESTful APIs with serialization and authentication.
      
      JWT Authentication: Secure, stateless authentication using djangorestframework-simplejwt.
      
      Cloudinary: Handles resume file uploads securely and efficiently.
      
      Django Filter: Enables flexible filtering for job browsing.
      
      SQLite: Lightweight database for development (can be swapped for PostgreSQL in production).


**Endpoints**

      Users: /api/users/ (signup, restricted list/retrieve)
      
      Jobs: /api/jobs/ (create, update, delete, browse, retrieve)
      
      Applications: /api/applications/ (create, list, update status)
      
      Token: /api/token/ (login), /api/token/refresh/ (refresh token)


**Notes**

      The API enforces role-based access (applicant/company) and ownership checks.
      
      Pagination is enabled with a default page size of 10.
      
      Resume uploads are validated to ensure PDF format and stored on Cloudinary.
      
      Unit tests cover key functionality (signup, login, job creation, etc.).
