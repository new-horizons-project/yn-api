<img width="128" height="128" alt="New Horizons Project" align="right" src="https://github.com/user-attachments/assets/20781c4e-65a1-4846-946c-c5d318b65360" />

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/elasticsearch-%230377CC.svg?style=for-the-badge&logo=elasticsearch&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)

# New Horizons API

###### The New Way of Storing Knowledge

### About

New Horizons API is the backend server for the New Horizons service, responsible for processing, computing, and storing all application data.

## Installation and Running

### Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

---

### Using Docker

1. **Clone the repository**
```bash
git clone https://github.com/new-horizons-project/yn-api.git
cd yn-api
````

2. **Set up environment variables**

* Copy the example environment file:

```bash
cp .env.example .env
```

* Edit `.env` to configure your database credentials, API settings, etc.

3. **Start the application**

```bash
docker-compose up --build -d
```

### Notes

* Make sure PostgreSQL credentials in `.env` match the `docker-compose.yaml` configuration.
* Logs can be viewed with:

```bash
docker-compose logs -f
```

* The API is available at port `9002` by default

## Credits

This project uses following open-source libraries:

| Package               | License                    |
|-----------------------|----------------------------|
| **FastAPI**           | MIT                        |
| **SQLAlchemy**        | MIT                        |
| **asyncpg**           | Apache 2.0                 |
| **PyJWT**             | MIT                        |
| **passlib**           | BSD                        |
| **Pydantic**          | MIT                        |
| **pydantic-settings** | MIT                        |
| **Colorama**          | BSD                        |

Special thanks to the authors and maintainers of these libraries for their contributions to the open-source community.

### Development Team

| Role                    | Contributor |
|-------------------------|-------------|
| Lead Backend Developer  | [@at-elcapitan](https://github.com/at-elcapitan) |
| Backend Developer       | [@phantom42-web](https://github.com/phantom42-web) |

