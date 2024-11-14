import subprocess #untuk mengontrol input dan output
import time

#Check Function 
def wait_for_postgres(host, max_retries=5, delay_seconds=5):
    """Menunggu PostgreSQL agar siap menerima koneksi."""
    retries = 0  # Inisialisasi jumlah percobaan koneksi

    # Loop utama, akan mencoba koneksi hingga mencapai batas max_retries
    while retries < max_retries:
        try:
            # Menjalankan perintah 'pg_isready' untuk mengecek koneksi PostgreSQL
            result = subprocess.run(
                ["pg_isready", "-h", host],  # Perintah yang dijalankan
                check=True,  # Raise error jika perintah gagal
                capture_output=True,  # Tangkap output dari perintah
                text=True  # Output dikembalikan dalam bentuk teks
            )
            # Mengecek apakah PostgreSQL menerima koneksi dengan memeriksa output
            if "accepting connections" in result.stdout:
                print("Successfully connected to PostgreSQL!")
                return True  # Mengembalikan True jika berhasil terhubung
        except subprocess.CalledProcessError as e:
            # Jika koneksi gagal, tampilkan pesan error
            print(f"Error connecting to PostgreSQL: {e}")
            retries += 1  # Tambah jumlah percobaan

            # Tampilkan pesan retry dengan informasi percobaan saat ini
            print(
                f"Retrying in {delay_seconds} seconds... (Attempt {retries}/{max_retries})"
            )
            time.sleep(delay_seconds)  # Tunggu sebelum mencoba lagi

    # Jika mencapai max_retries namun belum berhasil, tampilkan pesan dan return False
    print("Max retries reached. Exiting.")
    return False  # Mengembalikan False jika koneksi tidak berhasil

# Menggunakan fungsi wait_for_postgres sebelum menjalankan proses ELT
# Jika tidak berhasil terhubung ke PostgreSQL, keluar dari script dengan kode status 1
if not wait_for_postgres(host="source_postgres"):
    exit(1)

# Jika berhasil, lanjutkan dan tampilkan pesan untuk memulai proses ELT
print("Starting ELT script...")

# Konfigurasi untuk database sumber (PostgreSQL)
source_config = {
    'dbname': 'source_db',         # Nama database sumber
    'user': 'postgres',            # Nama pengguna untuk database sumber
    'password': 'secret',          # Password untuk database sumber
    'host': 'source_postgres'      # Nama host atau service dari PostgreSQL sumber (sesuai dengan docker-compose)
}

# Konfigurasi untuk database tujuan (PostgreSQL)
destination_config = {
    'dbname': 'destination_db',     # Nama database tujuan
    'user': 'postgres',             # Nama pengguna untuk database tujuan
    'password': 'secret',           # Password untuk database tujuan
    'host': 'destination_postgres'  # Nama host atau service dari PostgreSQL tujuan (sesuai dengan docker-compose)
}

# Membuat perintah untuk melakukan dump dari database sumber menggunakan pg_dump
dump_command = [
    'pg_dump',                      # Command-line tool untuk PostgreSQL dump
    '-h', source_config['host'],    # Host dari database sumber
    '-U', source_config['user'],    # User dari database sumber
    '-d', source_config['dbname'],  # Nama database sumber
    '-f', 'data_dump.sql',          # File output untuk menyimpan dump data
    '-w'                            # Opsi untuk tidak meminta password secara interaktif
]

# Menyiapkan variabel lingkungan (environment) PGPASSWORD agar password tidak perlu diinput manual
subprocess_env = dict(PGPASSWORD=source_config['password'])

# Menjalankan perintah dump dengan konfigurasi environment untuk password
subprocess.run(dump_command, env=subprocess_env, check=True)

# Membuat perintah untuk memuat file SQL hasil dump ke dalam database tujuan menggunakan psql
load_command = [
    'psql',                         # Command-line tool untuk PostgreSQL load
    '-h', destination_config['host'],  # Host dari database tujuan
    '-U', destination_config['user'],  # User dari database tujuan
    '-d', destination_config['dbname'],  # Nama database tujuan
    '-a', '-f', 'data_dump.sql'     # File dump SQL yang akan dimuat
]

# Mengatur variabel environment PGPASSWORD untuk database tujuan agar password tidak perlu diinput manual
subprocess_env = dict(PGPASSWORD=destination_config['password'])

# Menjalankan perintah load dengan konfigurasi environment untuk password
subprocess.run(load_command, env=subprocess_env, check=True)

# Menampilkan pesan bahwa proses ELT telah selesai
print("Ending ELT script...")