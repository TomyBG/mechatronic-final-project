import math
import os
import sys

# הוספת תיקיית השורש לנתיב כדי שנוכל לייבא את מסד הנתונים
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)
if base_dir not in sys.path:
    sys.path.append(base_dir)

# יבוא מחלקת מסד הנתונים החדשה שלנו
try:
    from catalog.Database import Database
except ImportError:
    try:
        from Database import Database
    except ImportError:
        from components.Database import Database

class IrrigationCalculator:
    def __init__(self, db_path=None):
        if db_path is None:
            # מנסה למצוא את קובץ מסד הנתונים במיקומים האפשריים
            path1 = os.path.join(base_dir, "catalog", "components.db")
            path2 = os.path.join(base_dir, "components", "components.db")
            
            if os.path.exists(path1):
                self.db_path = path1
            elif os.path.exists(path2):
                self.db_path = path2
            else:
                self.db_path = path1 # ברירת מחדל
        else:
            self.db_path = db_path
            
        self.KINEMATIC_VISCOSITY = 1.004e-6
        self.MIN_END_PRESSURE = 1.0
        self.SAFETY_MARGIN = 1.15
        
        self.K_ELBOW = 1.3
        self.K_TEE = 1.8
        self.K_CONNECTOR = 0.5

    def get_length_classification(self, length_m):
        lower = (int(length_m) // 10) * 10
        upper = lower + 10
        return f"Range: {lower}-{upper}m"

    def _select_main_pipe_by_rules(self, length_m):
        if length_m <= 60: nominal = 16
        elif length_m <= 100: nominal = 25
        else: nominal = 32
        
        # התחברות ל-DB ושליפת הקוטר הפנימי המדויק לטובת חישובי מכניקת זורמים
        db = Database(self.db_path)
        pipe_data = db.get_pipe_by_diameter(nominal)
        
        if pipe_data:
            # אינדקס 4 הוא ה- internal_diameter_mm כפי שהוגדר בטבלה
            internal = pipe_data[4] 
        else:
            # מקדם גיבוי למקרה שהצינור לא קיים בטבלה
            internal = nominal * 0.85 
            
        return nominal, internal

    def _select_spaghetti_by_main(self, main_pipe_mm):
        if main_pipe_mm == 16: return "5mm"
        elif main_pipe_mm == 25: return "6mm"
        elif main_pipe_mm >= 32: return "7mm"
        return "5mm"

    def _calculate_dripper_combo(self, target_flow):
        available_drippers = [8.0, 4.0, 2.0, 1.0]
        
        # טיפול במקרה קצה של זרימה נמוכה מאוד
        if target_flow <= 1.0:
            return "1x (1.0 L/h)", 1.0

        best_combo = [1.0] # ערך התחלתי שרירותי
        min_diff = abs(1.0 - target_flow)

        # 1. בדיקת טפטפת בודדת
        for d1 in available_drippers:
            diff = abs(d1 - target_flow)
            if diff < min_diff:
                min_diff = diff
                best_combo = [d1]

        # 2. בדיקת שילוב של 2 טפטפות
        for d1 in available_drippers:
            for d2 in available_drippers:
                total = d1 + d2
                diff = abs(total - target_flow)
                if diff < min_diff:
                    min_diff = diff
                    best_combo = [d1, d2]
        
        # 3. בדיקת שילוב של 3 טפטפות
        for d1 in available_drippers:
            for d2 in available_drippers:
                for d3 in available_drippers:
                    total = d1 + d2 + d3
                    diff = abs(total - target_flow)
                    if diff < min_diff:
                        min_diff = diff
                        best_combo = [d1, d2, d3]
        
        # יצירת הטקסט הסופי שיוצג למשתמש והחישוב של הזרימה בפועל
        actual_flow = sum(best_combo)
        combo_str = "+".join([str(d) for d in best_combo])
        
        return f"{len(best_combo)}x ({combo_str} L/h)", actual_flow

    def _calc_velocity(self, flow_lh, internal_diameter_mm):
        if flow_lh <= 0: return 0
        q_m3s = flow_lh / 3_600_000
        d_m = internal_diameter_mm / 1000.0
        area = math.pi * ((d_m / 2) ** 2)
        return q_m3s / area

    def _calc_friction_factor(self, velocity, internal_diameter_mm):
        if velocity < 0.01: return 0.03, 0 # Return f, Re
        d_m = internal_diameter_mm / 1000.0
        re = (velocity * d_m) / self.KINEMATIC_VISCOSITY
        
        if re < 2000: 
            return 64 / re, re
        elif re < 100000: 
            return 0.3164 / (re ** 0.25), re
        else: 
            return 0.02, re

    def _calc_segment_loss(self, flow_lh, internal_diameter_mm, length_m, k_loss_per_segment=0):
        if flow_lh <= 0: return 0, 0, 0, 0 # loss, velocity, f, Re
        
        velocity = self._calc_velocity(flow_lh, internal_diameter_mm)
        f, re = self._calc_friction_factor(velocity, internal_diameter_mm)
        d_m = internal_diameter_mm / 1000.0
        g = 9.81
        
        friction_head_m = f * (length_m / d_m) * (velocity**2) / (2 * g)
        minor_head_m = k_loss_per_segment * (velocity**2) / (2 * g)
        
        total_loss_bar = (friction_head_m + minor_head_m) / 10.197
        return total_loss_bar, velocity, f, re

    def calculate_planters_scenario(self, length_m, num_planters, specific_flows_list, connectors):
        nominal_dia, internal_dia = self._select_main_pipe_by_rules(length_m)
        spaghetti_type = self._select_spaghetti_by_main(nominal_dia)
        
        planter_details_list = []
        actual_flows_list = []
        
        if not specific_flows_list:
            specific_flows_list = [2.0] * num_planters
            
        for i in range(num_planters):
            target = specific_flows_list[i] if i < len(specific_flows_list) else 2.0
            desc, actual = self._calculate_dripper_combo(target)
            planter_details_list.append(f"Planter {i+1} (Req: {target}L): {spaghetti_type} -> {desc} = {actual}L/h")
            actual_flows_list.append(actual)
            
        total_flow = sum(actual_flows_list)
        
        total_k = (connectors.get('elbows', 0) * self.K_ELBOW) + \
                  (connectors.get('tees', 0) * self.K_TEE) + \
                  (connectors.get('straights', 0) * self.K_CONNECTOR)
        
        k_per_segment = total_k / num_planters if num_planters > 0 else 0
        dist_between = length_m / num_planters
        
        current_flow = total_flow
        cumulative_loss = 0
        
        graph_x = [0]
        graph_loss = [0]
        debug_info = {}
        
        for i in range(num_planters):
            loss, v, f, re = self._calc_segment_loss(current_flow, internal_dia, dist_between, k_per_segment)
            
            if i == 0:
                debug_info = {
                    "velocity": v,
                    "reynolds": re,
                    "friction_f": f,
                    "segment_flow": current_flow,
                    "segment_loss": loss,
                    "internal_dia": internal_dia
                }

            cumulative_loss += loss
            graph_x.append((i + 1) * dist_between)
            graph_loss.append(cumulative_loss)
            
            flow_out = actual_flows_list[i] if i < len(actual_flows_list) else 0
            current_flow -= flow_out
            if current_flow < 0: current_flow = 0
            
        required_inlet = (self.MIN_END_PRESSURE + cumulative_loss) * self.SAFETY_MARGIN
        
        graph_y = []
        for loss in graph_loss:
            graph_y.append(round(required_inlet - loss, 3))

        return {
            "type": "planters_scenario",
            "range_classification": self.get_length_classification(length_m),
            "recommended_main_pipe_mm": nominal_dia,
            "recommended_planter_pipe": spaghetti_type,
            "detailed_planters_list": planter_details_list,
            "total_flow_lh": round(total_flow, 2),
            "required_inlet_pressure_bar": round(required_inlet, 3),
            "graph_data": {"x": graph_x, "y": graph_y},
            "debug_info": debug_info
        }

    def calculate_continuous_soil(self, length_m, total_flow_lh, connectors):
        nominal_dia, internal_dia = self._select_main_pipe_by_rules(length_m)
        
        segments = 50 
        segment_len = length_m / segments
        flow_drop_per_segment = total_flow_lh / segments
        
        total_k = (connectors.get('elbows', 0) * self.K_ELBOW) + \
                  (connectors.get('tees', 0) * self.K_TEE) 
        k_per_segment = total_k / segments

        current_flow = total_flow_lh
        cumulative_loss = 0
        graph_x = [0]
        graph_loss = [0]
        
        debug_info = {}

        for i in range(segments):
            loss, v, f, re = self._calc_segment_loss(current_flow, internal_dia, segment_len, k_per_segment)
            
            if i == 0:
                 debug_info = {
                    "velocity": v,
                    "reynolds": re,
                    "friction_f": f,
                    "segment_flow": current_flow,
                    "segment_loss": loss,
                    "internal_dia": internal_dia
                }
            
            cumulative_loss += loss
            current_flow -= flow_drop_per_segment
            if current_flow < 0: current_flow = 0
            
            graph_x.append((i + 1) * segment_len)
            graph_loss.append(cumulative_loss)

        required_inlet = (self.MIN_END_PRESSURE + cumulative_loss) * self.SAFETY_MARGIN
        graph_y = [round(required_inlet - l, 3) for l in graph_loss]

        return {
            "type": "continuous",
            "range_classification": self.get_length_classification(length_m),
            "recommended_pipe_mm": nominal_dia,
            "total_flow_lh": round(total_flow_lh, 2),
            "required_inlet_pressure_bar": round(required_inlet, 3),
            "graph_data": {"x": graph_x, "y": graph_y},
            "debug_info": debug_info
        }