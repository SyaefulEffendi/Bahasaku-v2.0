from app import create_app

app = create_app()

if __name__ == '__main__':
    # Port diubah ke 5000 agar sesuai dengan Dockerfile dan docker-compose.yml
    # Debug=True diaktifkan agar auto-reload saat ada perubahan code
    app.run(host='0.0.0.0', port=5000, debug=True)