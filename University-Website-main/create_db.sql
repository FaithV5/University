-- create_db.sql
DROP DATABASE IF EXISTS univdb;
CREATE DATABASE univdb;
USE univdb;

-- users: admins and instructors
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','instructor') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- departments
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

-- programs (admin can add)
CREATE TABLE programs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dept_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(id) ON DELETE CASCADE
);

-- courses (admin can add)
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL
);

-- students
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    dept_id INT NOT NULL,
    program_id INT,
    course_id INT,
    semester VARCHAR(20),
    grade VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE SET NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
);

-- seed departments
INSERT INTO departments (code, name) VALUES
('CAFAD','CAFAD'),
('CET','CET'),
('CICS','CICS'),
('CoE','CoE');

-- seed programs (initial)
-- CAFAD programs
INSERT INTO programs (dept_id, name) VALUES
((SELECT id FROM departments WHERE code='CAFAD'),'Bachelor of Fine Arts and Design Major in Visual Communication'),
((SELECT id FROM departments WHERE code='CAFAD'),'Bachelor of Science in Architecture'),
((SELECT id FROM departments WHERE code='CAFAD'),'Bachelor of Science in Interior Design');

-- CET programs
INSERT INTO programs (dept_id, name) VALUES
((SELECT id FROM departments WHERE code='CET'),'Bachelor of Civil Engineering Technology'),
((SELECT id FROM departments WHERE code='CET'),'Bachelor of Computer Engineering Technology'),
((SELECT id FROM departments WHERE code='CET'),'Bachelor of Mechanical Engineering Technology');

-- CICS programs
INSERT INTO programs (dept_id, name) VALUES
((SELECT id FROM departments WHERE code='CICS'),'Bachelor of Science in Computer Science'),
((SELECT id FROM departments WHERE code='CICS'),'Bachelor of Science in Information Technology');

-- CoE programs
INSERT INTO programs (dept_id, name) VALUES
((SELECT id FROM departments WHERE code='CoE'),'Bachelor of Science in Civil Engineering'),
((SELECT id FROM departments WHERE code='CoE'),'Bachelor of Science in Computer Engineering'),
((SELECT id FROM departments WHERE code='CoE'),'Bachelor of Science in Mechanical Engineering');

-- seed few courses
INSERT INTO courses (code, name) VALUES
('IT111','Introduction to Computing'),
('CS111','Introduction to Programming'),
('CS131','Data Structures and Algorithms');

-- The users are inserted by app on first run if table empty (so passwords are hashed).
