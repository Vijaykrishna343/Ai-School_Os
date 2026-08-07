# Database Design

## Core Entities
- School
- Academic Year
- Class
- Section
- Parent
- Student
- Enrollment
- Teacher

## Relationships
- One School → Many Academic Years
- One School → Many Classes
- One Parent → Many Students
- One Student → Many Enrollments
- One Academic Year → Many Enrollments
- One Class → Many Enrollments

## Business Rules
- Admission Number is permanent.
- Roll Number changes every academic year.
- Students are never deleted.
- One parent can have multiple students.
- Only one academic year is active.
- Promotions create a new enrollment.


# Database Design

## Project Vision

## Core Entities

## Entity Relationships

## Business Rules

## Student Lifecycle

## Parent Design

## Branch Design

## Development Standards