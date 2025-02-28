# Title Hunt

Flask Portal, Fast API backend, DB for Title Hunt

1. Run

```bash
poetry install
```

2. Create '.env' file (simply copy file .env.sample):

3. Run

```bash
docker compose up d db
```

to create an docker container

4. Development and debugging

   This project contains both Flask and FastAPI.

   To run Flask app:

   - go to "Run and Debug" tab in VSCode and select "Python:Flask" from dropdown menu

   To run FastAPI app:

   - go to "Run and Debug" tab in VSCode and select "API" from dropdown menu

   After selection, press `"Run and Debug"` button or `F5` key on keyboard

5. Create db with command

```bash
flask db upgrade
```

6. add credentials.json for Google export sheet

7. In main folder need install node_modules to work with tailwind, run

```bash
yarn
```

## Commands to get data into your local db:

Go to `ssh s2b` and take the backup file from our server and put it in your environment:

```bash
cp /home/runner/[folder]/backup/db_2024-10-29T10:35:27Z.tgz .
```

```bash
mv db_2024-10-29T10:35:27Z.tgz dump.tgz
```

In our project, download dump.tgz:

```bash
scp s2b:dump.tgz .
```

```bash
tar xvzf dump.tgz
```

Clear db and fill with data:

```bash
dcdn -v db
```

```bash
dcupd db
```

```bash
flask db upgrade
```

```bash
flask create-admin
```

```bash
flask fill-db-with-actors
```

```bash
flask fill-db-with-directors
```

```bash
flask fill-db-with-genres
```

```bash
flask fill-db-with-subgenres
```

```bash
flask fill-db-with-movies
```

```bash
dce -T db psql < dump.sql
```

Export from Google sheets (Excel)

1. Delete token.json if old (expiered) (error about grand value invalid or smth...)
2. Go to Google Console
   https://console.cloud.google.com/apis/credentials?invt=AbigJA&project=title-hunter-442908
3. Create Project
4. Go to Library and add APIs - Google Drive Api, Google Sheet Api
5. Update consent screen and add this scopes
6. Add User! to TEST list! (I don't now why this need because its I owner/developer...)
   (I don't know if scopes needed bacause I got error only about test user)
7. Create Credentials for Desktop! and download JSON -> {"installed": {...}}

8. Add Excel ID (from URL) to SPREADSHEET_ID in project.env and config.py (also add RANGE_NAME, its first tab in the sheet)
   https://docs.google.com/spreadsheets/d/[.....SPREADSHEET_ID.....]/edit?hl=ru&gid=0#gid=0
9. Change permission to "Everyone with url can use".

10. Run command flask fill-db-with-jobs
    (if no token.json)
11. Go to URL, select account with TEST User (6)
12. In last page "Make sure you trust App Name" copy Authorization code - 4/...id...

---

free -h # Check RAM usage
lscpu # Check CPU details
df -h # Check disk space

https://www.youtube.com/watch?v=Zem1H7Rr9yM&t=1271s
https://www.youtube.com/watch?v=mZbLvGQqEvY&t=158s

---

Add permission
chmod 0400 test-two-key.pem
ssh -i test-two-key.pem ubuntu@13.49.57.228

1. sudo apt-get update

2. 1 and 2
   https://docs.docker.com/engine/install/ubuntu/#:~:text=Set%20up%20Docker%27s,repository.

Remove sudo:
(sudo groupadd docker - if no)
sudo usermod -aG docker $USER
newgrp docker

Add ZSH and docker alias (dcps)
sudo apt install zsh -y
zsh --version
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
vi ~/.zshrc
plugins=(git docker docker-compose)
(exit and enter)

(only work from ssh localy)
docker login -u
docker pull azalor/title-hunter-backend:latest
docker pull azalor/title-hunter-frontend:latest

touch docker-compose.yml
touch .env

Run commands to fill DB
dce app poetry run flask shell
dce app poetry run flask create-admin
dce app poetry run flask execute-all
dce app poetry run flask calculate-movie-rating

If codebase changed:
first build and push
docker build -t title-hunter-frontend:latest .
docker tag title-hunter-frontend:latest azalor/title-hunter-frontend:latest
docker push azalor/title-hunter-frontend:latest

BUILD PUSH AND PULL - try with lates?
docker build -t azalor/title-hunter-backend .
docker push azalor/title-hunter-backend
docker pull azalor/title-hunter-backend

Help in frontend to BUILD AND PUSH Docker
docker build -t azalor/title-hunter-frontend:latest .
docker push azalor/title-hunter-frontend:latest
docker pull azalor/title-hunter-frontend:latest
