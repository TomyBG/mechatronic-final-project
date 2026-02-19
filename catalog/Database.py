"""
Component Catalog Module
SQLite database for storing pipes, drippers, fittings, and other components
"""

import sqlite3
import os

class Database:
    """
    Manages the component database (pipes, drippers, fittings)
    """
    
    def __init__(self, db_path="catalog/components.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with all component tables"""
        if not os.path.exists(self.db_path):
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            # ===== PIPES TABLE =====
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipes (
                    id INTEGER PRIMARY KEY,
                    pipe_type TEXT NOT NULL,
                    nominal_diameter_mm REAL NOT NULL,
                    wall_thickness_mm REAL NOT NULL,
                    internal_diameter_mm REAL NOT NULL,
                    flow_type TEXT NOT NULL,
                    notes TEXT
                )
            """)
            
            # ===== DRIPPERS TABLE =====
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drippers (
                    id INTEGER PRIMARY KEY,
                    dripper_type TEXT NOT NULL,
                    flow_rates TEXT NOT NULL,
                    physical_type TEXT NOT NULL,
                    exponent_x REAL NOT NULL,
                    min_pressure_bar REAL NOT NULL,
                    max_pressure_bar REAL NOT NULL,
                    notes TEXT
                )
            """)
            
            # ===== FITTINGS TABLE =====
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fittings (
                    id INTEGER PRIMARY KEY,
                    fitting_name TEXT NOT NULL,
                    engineering_symbol TEXT NOT NULL,
                    k_value_small REAL NOT NULL,
                    k_value_large REAL NOT NULL,
                    description TEXT
                )
            """)
            
            # Insert default pipes data
            pipes_data = [
                ("צינורית (Spaghetti)", 5.0, 1.0, 3.0, "למינרית/טורבולנטית", "לחיבור אביזרי קצה בלבד"),
                ("צינור 16 (סטנדרט)", 16.0, 1.2, 13.6, "טורבולנטית", 'הצינור הכי נפוץ ("מוביל")'),
                ("צינור 20", 20.0, 1.4, 17.2, "טורבולנטית", "לשלוחות ארוכות"),
                ("צינור 25", 25.0, 1.5, 22.0, "טורבולנטית", "קו ראשי לגינה בינונית"),
                ("צינור 32", 32.0, 2.0, 28.0, "טורבולנטית", "קו ראשי / מוביל מים"),
                ("צינור 50", 50.0, 3.0, 44.0, "טורבולנטית", "קו ראשי לחקלאות/פארקים"),
                ("צינור 63", 63.0, 3.8, 55.4, "טורבולנטית", "קו ראשי למרחקים גדולים"),
            ]
            
            for pipe in pipes_data:
                cursor.execute("""
                    INSERT INTO pipes 
                    (pipe_type, nominal_diameter_mm, wall_thickness_mm, internal_diameter_mm, flow_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, pipe)
            
            # Insert default drippers data
            drippers_data = [
                ("טפטפת נעץ (Button)", "1.0/2.0 / 4.0 / 8.0 L/h", "חיצונית לצינור", 0.5, 1.0, 4.0, "תלוי דגם"),
            ]
            
            for dripper in drippers_data:
                cursor.execute("""
                    INSERT INTO drippers 
                    (dripper_type, flow_rates, physical_type, exponent_x, min_pressure_bar, max_pressure_bar, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, dripper)
            
            # Insert default fittings data
            fittings_data = [
                ("מחבר שן (Coupling)", "=", 0.6, 0.4, "חיבור ישר בין צינורות"),
                ("זווית 90 (Elbow)", "L", 1.3, 1.1, "שינוי כיוון 90 מעלות"),
                ("הסתעפות T (זרימה ישרה)", "T-run", 0.6, 0.5, "המשך ישר עם ענף צד"),
                ("הסתעפות T (פנייה)", "T-branch", 1.8, 1.5, "פנייה בזווית מהקו הראשי"),
                ("כניסה לצינור (Saddle/Start)", "Inlet", 0.8, 0.6, "התחלת קו מהמקור"),
            ]
            
            for fitting in fittings_data:
                cursor.execute("""
                    INSERT INTO fittings 
                    (fitting_name, engineering_symbol, k_value_small, k_value_large, description)
                    VALUES (?, ?, ?, ?, ?)
                """, fitting)
            
            connection.commit()
            connection.close()
    
    def get_all_pipes(self):
        """Retrieve all pipes from catalog"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM pipes")
        pipes = cursor.fetchall()
        connection.close()
        return pipes
    
    def get_pipe_by_diameter(self, diameter):
        """Get pipe specifications by nominal diameter"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM pipes WHERE nominal_diameter_mm = ?", (diameter,))
        pipe = cursor.fetchone()
        connection.close()
        return pipe
    
    def get_all_drippers(self):
        """Retrieve all drippers from catalog"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM drippers")
        drippers = cursor.fetchall()
        connection.close()
        return drippers
    
    def get_all_fittings(self):
        """Retrieve all fittings from catalog"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM fittings")
        fittings = cursor.fetchall()
        connection.close()
        return fittings
    
    def add_custom_pipe(self, pipe_type, nominal_diameter, wall_thickness, internal_diameter, flow_type, notes=""):
        """Add custom pipe to catalog"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO pipes 
            (pipe_type, nominal_diameter_mm, wall_thickness_mm, internal_diameter_mm, flow_type, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pipe_type, nominal_diameter, wall_thickness, internal_diameter, flow_type, notes))
        connection.commit()
        connection.close()
    
    def add_custom_dripper(self, dripper_type, flow_rates, physical_type, exponent_x, min_pressure, max_pressure, notes=""):
        """Add custom dripper to catalog"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO drippers 
            (dripper_type, flow_rates, physical_type, exponent_x, min_pressure_bar, max_pressure_bar, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (dripper_type, flow_rates, physical_type, exponent_x, min_pressure, max_pressure, notes))
        connection.commit()
        connection.close()
    
    def add_custom_fitting(self, fitting_name, engineering_symbol, k_value_small, k_value_large, description=""):
        """Add custom fitting to catalog"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO fittings 
            (fitting_name, engineering_symbol, k_value_small, k_value_large, description)
            VALUES (?, ?, ?, ?, ?)
        """, (fitting_name, engineering_symbol, k_value_small, k_value_large, description))
        connection.commit()
        connection.close()