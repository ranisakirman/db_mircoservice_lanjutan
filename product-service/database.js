const { Sequelize } = require('sequelize');

// Membuat koneksi ke database MySQL
const sequelize = new Sequelize('product-db', 'root', 'root', {
    host: process.env.DB_HOST,  // Host database yang akan digunakan
    dialect: 'mysql',           // Jenis database yang digunakan
    port: 3306                  // Port default MySQL
});

module.exports = sequelize;