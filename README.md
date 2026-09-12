# Portfolio + Blog (Django)

A Django application named `portfolio`, built on top of the Bootstrap 5 **TemplateMo Topic Listing** theme.

## Requirements

* Python 3.10+

## Installation & Local Setup

```bash
# 1) Create a virtual environment

python -m venv .venv

source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2) Install dependencies

pip install -r requirements.txt

# 3) Create and apply migrations

python manage.py makemigrations portfolio

python manage.py migrate

# 4) Create an admin user

python manage.py createsuperuser

# 5) Run the development server

python manage.py runserver
```

After running the server:

* Website: http://127.0.0.1:8000/
* Admin panel: http://127.0.0.1:8000/admin/

## First Steps After Launching the Website

From the admin panel:

1. Create a **Profile** record (name, role, bio, avatar, resume, location, and email), along with the Social Links, Experiences, and Skills associated with the profile using inline forms.

2. Create several **Tags**.

3. Add several **Projects** to the Work section, with dedicated gallery images using inline forms.

4. Add several **Posts** to the Blog section using the following categories: Design, Graphic, Marketing, Finance, Music, and Education. Enable the `featured` checkbox for posts that should appear on the homepage.

5. Add several **GalleryImage** records for the Gallery page.

Contact form submissions from `/contact/` are automatically stored in the **ContactMessage** model and can be viewed from the admin panel.

## Project Structure

```text
manage.py

config/                  # Django configuration (settings, urls, wsgi, asgi)

portfolio/               # Main application
    models.py            # Profile, SocialLink, Experience, Skill, Tag, Project,
                         # ProjectImage, Post, GalleryImage, ContactMessage
    admin.py             # Registers all models in the admin panel
    views.py / urls.py   # Views and URL routes
    forms.py             # ContactForm (ModelForm)
    context_processors.py # Makes the profile available in all templates
    templates/portfolio/ # HTML templates (based on the TemplateMo theme)

static/portfolio/        # Theme static files (CSS/JS/fonts/images)

media/                   # Uploaded files (avatars, project images, resumes, etc.)
```

## URLs

| URL                       | Description                                                                                         |
| ------------------------- | --------------------------------------------------------------------------------------------------- |
| `/`                       | Home — featured posts + category tabs                                                               |
| `/about/`                 | About Me                                                                                            |
| `/work/`, `/work/<slug>/` | Project list and project details                                                                    |
| `/blog/`, `/blog/<slug>/` | Post list and post details (pagination + keyword search `?keyword=` + category filter `?category=`) |
| `/gallery/`               | Gallery                                                                                             |
| `/contact/`               | Functional contact form (POST → saves data to the database)                                         |
| `/admin/`                 | Admin panel                                                                                         |

## Notes About This Version

This project was developed in an environment without internet access, so Django/Pillow were not installed or tested on an actual server.

The following tests and checks were performed:

* Syntax compilation of all Python files (`py_compile`) — no errors.
* Verification of all `{% url %}` tags in the templates against the URL names defined in `urls.py`.
* Verification of all fields and methods used in the templates (`profile.x`, `post.x`, `project.x`, etc.) against the models defined in `models.py`.
* Verification of the context keys provided by each view against the variables expected by its corresponding template.
* Verification of balanced `{% %}` and `{{ }}` template tags across all templates.

After installing Django on your system and running `migrate`, it is recommended to check all pages thoroughly in a web browser. If you encounter any issues, such as a minor typo or configuration problem, they can be fixed accordingly.
