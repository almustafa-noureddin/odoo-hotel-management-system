<div align="center">

# Odoo Hotel Management System

**A comprehensive, all-in-one hotel management and booking system built on the Odoo 18 platform.**

</div>

![Work in Progress](https://img.shields.io/badge/Status-Work%20In%20Progress-yellow.svg)
![Odoo Version](https://img.shields.io/badge/Odoo-18.0-blue.svg)
![License](https://img.shields.io/badge/License-LGPL--3-green.svg)

---

## Overview

This project is an Odoo 18 module designed to provide a single, integrated solution for mid-sized hotels and hotel chains. It aims to solve the common challenge of fragmented systems by unifying reservations, housekeeping, guest billing, and a public-facing booking website into one cohesive ecosystem. By centralizing operations, the system will reduce administrative overhead, eliminate booking conflicts, and create a seamless experience for both staff and guests.

**This is a portfolio project currently under active development.** The features and functionalities listed below are part of the project roadmap and will be implemented incrementally.

---

## Key Features (Planned & Implemented)

The system is designed to be modular, allowing for a phased implementation of features.

-   [ ] **Core Data Models:**
    -   [x] Hotel Properties & Room Types
    -   [x] Individual Room Management
    -   [ ] Rate & Pricing Engine
-   [ ] **Reservation & Booking Management:**
    -   [ ] Visual Booking Calendar (Day/Week/Month views)
    -   [ ] Create, Update, Cancel Bookings
    -   [ ] Automated Double-Booking Prevention
    -   [ ] Group Bookings
-   [ ] **Front Desk Operations:**
    -   [ ] Streamlined Guest Check-in / Check-out
    -   [ ] Centralized Guest Folio for all charges
    -   [ ] Automated Invoice Generation
-   [ ] **Housekeeping Automation:**
    -   [ ] Room Status Tracking (`Clean`, `Needs Cleaning`, `Maintenance`)
    -   [ ] Automated Task Generation post-checkout
    -   [ ] Housekeeper Assignments & Mobile View
-   [ ] **Integrations:**
    -   [ ] **Odoo POS:** Charge restaurant/bar bills directly to a guest's room.
    -   [ ] **Odoo Website:** A public portal for guests to search, book, and pay for rooms.
    -   [ ] **Payment Gateways:** Stripe & PayPal for online booking deposits.
    -   [ ] **Communication:** Automated booking confirmation emails.

---

## Technology Stack

* **Framework:** Odoo 18 (Community Edition)
* **Language:** Python 3.10+
* **Database:** PostgreSQL
* **Frontend:** XML, Owl Framework (Odoo's Frontend Engine)

---

## Project Roadmap

This project is being developed following a phased approach:

1.  **Phase 1: Foundation & Data Modeling (In Progress)**
    * Setup development environment and core modules.
    * Define and implement the primary data models (`hotel.room`, `hotel.booking`, etc.).
2.  **Phase 2: Core Booking Functionality**
    * Develop backend logic for booking operations.
    * Implement the user interface and the booking calendar view.
3.  **Phase 3: Automation & Integration**
    * Automate check-in/check-out workflows and invoicing.
    * Integrate with Odoo Point of Sale.
4.  **Phase 4: Website & External Services**
    * Build the customer-facing website booking engine.
    * Integrate payment acquirers and email services.
5.  **Phase 5: Testing & Refinement**
    * Conduct end-to-end user acceptance testing (UAT).
    * Refine UI/UX and prepare for deployment.

---

## Installation

> **Note:** This module is not yet production-ready. These instructions are for a development setup.

1.  Clone this repository into your Odoo `addons` directory.
    ```bash
    git clone [https://github.com/almustafa-noureddin/odoo-hotel-management-system.git](https://github.com/almustafa-noureddin/odoo-hotel-management-system.git)
    ```
2.  Restart your Odoo server.
3.  Navigate to the `Apps` menu in Odoo.
4.  Click on `Update Apps List`.
5.  Search for "Hotel Management System" and click `Install`.

---

## Contributing

As this is a portfolio project, direct contributions are not the primary focus. However, feedback, suggestions, and constructive criticism are highly welcome. Please open an issue to share your thoughts or report a bug.

---

## License

This project is licensed under the **LGPL-3** License. See the `LICENSE` file for more details.