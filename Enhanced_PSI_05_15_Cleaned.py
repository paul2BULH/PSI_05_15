import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import json
import io
from enum import Enum

st.set_page_config(page_title="Enhanced PSI Web Debugger (PSI 05-15)", layout="wide")
st.title("🏥 Enhanced PSI 05–15 Analyzer + Debugger")
st.markdown("*Comprehensive Patient Safety Indicator Analysis with Advanced Logic*")

# Sidebar for configuration
with st.sidebar:
    st.header("🔧 Configuration")
    debug_mode = st.checkbox("Enable Debug Mode", value=True)
    show_exclusions = st.checkbox("Show Detailed Exclusions", value=True)
    validate_timing = st.checkbox("Enable Timing Validation", value=True)
    
    st.header("🎯 PSI Selection")
    selected_psis = st.multiselect(
        "Select PSIs to Analyze",
        ["PSI_05", "PSI_06", "PSI_07", "PSI_08", "PSI_09", "PSI_10", "PSI_11", "PSI_12", "PSI_13", "PSI_14", "PSI_15"],
        default=["PSI_13", "PSI_14", "PSI_15"]
    )

# Upload input and appendix files
col1, col2 = st.columns(2)
with col1:
    input_file = st.file_uploader("📁 Upload PSI Input Excel", type=[".xlsx"])
with col2:
    appendix_file = st.file_uploader("📋 Upload PSI Appendix Excel", type=[".xlsx"])

if input_file and appendix_file:
    try:
        # Load data with progress bar
        with st.spinner("Loading and processing data..."):
            df_input = pd.read_excel(input_file)
            appendix_df = pd.read_excel(appendix_file)

        # Extract and organize code sets (enhanced for PSI 13-15)
        code_sets = {}
        code_mapping = {
            # PSI 05 codes
            'FOREIID': 'FOREIID_CODES',
            # PSI 06 codes  
            'IATROID': 'IATROID_CODES',
            'IATPTXD': 'IATPTXD_CODES',
            'CTRAUMD': 'CTRAUMD_CODES',
            'PLEURAD': 'PLEURAD_CODES',
            # PSI 07 codes
            'IDTMC3D': 'IDTMC3D_CODES',
            'CANCEID': 'CANCEID_CODES',
            'IMMUNID': 'IMMUNID_CODES',
            # PSI 08 codes
            'FXID_CODES': 'FXID_CODES',
            'HIPFXID_CODES': 'HIPFXID_CODES',
            'PROSFXID': 'PROSFXID_CODES',
            # PSI 09 codes
            'POHMRI2D_CODES': 'POHMRI2D_CODES',
            'HEMOTH2P_CODES': 'HEMOTH2P_CODES',
            'COAGDID': 'COAGDID_CODES',
            'MEDBLEEDD': 'MEDBLEEDD_CODES',
            # PSI 10 codes
            'PHYSIDB_CODES': 'PHYSIDB_CODES',
            'DIALYIP_CODES': 'DIALYIP_CODES',
            'CARDIID': 'CARDIID_CODES',
            'CARDRID': 'CARDRID_CODES',
            'SHOCKID': 'SHOCKID_CODES',
            'CRENLFD': 'CRENLFD_CODES',
            # PSI 11 codes
            'ACURF2D': 'ACURF2D_CODES',
            'ACURF3D': 'ACURF3D_CODES',
            'PR9672P_CODES': 'PR9672P_CODES',
            'PR9671P_CODES': 'PR9671P_CODES',
            'PR9604P_CODES': 'PR9604P_CODES',
            'NEUROMD': 'NEUROMD_CODES',
            'MALHYPD': 'MALHYPD_CODES',
            # PSI 12 codes
            'DEEPVIB_CODES': 'DEEPVIB_CODES',
            'PULMOID_CODES': 'PULMOID_CODES',
            'HITD': 'HITD_CODES',
            'NEURTRAD': 'NEURTRAD_CODES',
            # PSI 13 codes
            'SEPTI2D': 'SEPTI2D_CODES',
            'INFECID': 'INFECID_CODES',
            # PSI 14 codes
            'RECLOIP': 'RECLOIP_CODES',
            'ABWALLCD': 'ABWALLCD_CODES',
            'ABDOMIPOPEN': 'ABDOMIPOPEN_CODES',
            'ABDOMIPOTHER': 'ABDOMIPOTHER_CODES',
            # PSI 15 codes - organ-specific
            'ABDOMI15P': 'ABDOMI15P_CODES',
            'SPLEEN15D': 'SPLEEN15D_CODES',
            'SPLEEN15P': 'SPLEEN15P_CODES',
            'ADRENAL15D': 'ADRENAL15D_CODES',
            'ADRENAL15P': 'ADRENAL15P_CODES',
            'VESSEL15D': 'VESSEL15D_CODES',
            'VESSEL15P': 'VESSEL15P_CODES',
            'DIAPHR15D': 'DIAPHR15D_CODES',
            'DIAPHR15P': 'DIAPHR15P_CODES',
            'GI15D': 'GI15D_CODES',
            'GI15P': 'GI15P_CODES',
            'GU15D': 'GU15D_CODES',
            'GU15P': 'GU15P_CODES',
            # Common codes
            'SURGI2R_CODES': 'SURGI2R_CODES',
            'MEDIC2R_CODES': 'MEDIC2R_CODES',
            'MDC14PRINDX': 'MDC14PRINDX_CODES',
            'MDC15PRINDX': 'MDC15PRINDX_CODES',
            'ORPROC': 'ORPROC_CODES'
        }

        for col in appendix_df.columns:
            col_clean = col.strip()
            if col_clean in code_mapping:
                codes = appendix_df[col].dropna().astype(str).str.replace(".", "", regex=False).str.upper().tolist()
                code_sets[code_mapping[col_clean]] = codes
            else:
                codes = appendix_df[col].dropna().astype(str).str.replace(".", "", regex=False).str.upper().tolist()
                code_sets[col_clean] = codes

        # Organ system mapping for PSI 15
        class OrganSystem(Enum):
            SPLEEN = "spleen"
            ADRENAL = "adrenal"  
            VESSEL = "vessel"
            DIAPHRAGM = "diaphragm"
            GASTROINTESTINAL = "gi"
            GENITOURINARY = "gu"

        def build_organ_system_mapping(code_sets):
            """Build organ system to code mapping for PSI 15"""
            return {
                OrganSystem.SPLEEN: {
                    'injury_codes': code_sets.get('SPLEEN15D_CODES', []),
                    'procedure_codes': code_sets.get('SPLEEN15P_CODES', [])
                },
                OrganSystem.ADRENAL: {
                    'injury_codes': code_sets.get('ADRENAL15D_CODES', []),
                    'procedure_codes': code_sets.get('ADRENAL15P_CODES', [])
                },
                OrganSystem.VESSEL: {
                    'injury_codes': code_sets.get('VESSEL15D_CODES', []),
                    'procedure_codes': code_sets.get('VESSEL15P_CODES', [])
                },
                OrganSystem.DIAPHRAGM: {
                    'injury_codes': code_sets.get('DIAPHR15D_CODES', []),
                    'procedure_codes': code_sets.get('DIAPHR15P_CODES', [])
                },
                OrganSystem.GASTROINTESTINAL: {
                    'injury_codes': code_sets.get('GI15D_CODES', []),
                    'procedure_codes': code_sets.get('GI15P_CODES', [])
                },
                OrganSystem.GENITOURINARY: {
                    'injury_codes': code_sets.get('GU15D_CODES', []),
                    'procedure_codes': code_sets.get('GU15P_CODES', [])
                }
            }

        organ_systems = build_organ_system_mapping(code_sets)

        # Enhanced data extraction functions
        def extract_dx_codes_enhanced(row):
            """Extract diagnoses with enhanced validation"""
            dx_list = []
            for i in range(1, 31):  # Support up to 30 diagnoses
                dx = row.get(f"DX{i}")
                poa = row.get(f"POA{i}")
                if pd.notna(dx) and str(dx).strip():
                    dx_clean = str(dx).replace(".", "").upper().strip()
                    poa_clean = str(poa).strip().upper() if pd.notna(poa) else ""
                    # Validate POA values
                    if poa_clean not in ["Y", "N", "U", "W", ""]:
                        poa_clean = ""
                    position = "PRINCIPAL" if i == 1 else "SECONDARY"
                    dx_list.append((dx_clean, poa_clean, position, i))
            return dx_list

        def extract_proc_info_enhanced(row):
            """Extract procedures with enhanced timing logic"""
            proc_list = []
            for i in range(1, 21):  # Support up to 20 procedures
                code = row.get(f"Proc{i}")
                date = row.get(f"Proc{i}_Date")
                time = row.get(f"Proc{i}_Time")
                if pd.notna(code) and str(code).strip():
                    code_clean = str(code).replace(".", "").upper().strip()
                    # Enhanced date parsing
                    dt = None
                    if pd.notna(date):
                        try:
                            if pd.notna(time):
                                dt_str = f"{date} {time}"
                                dt = pd.to_datetime(dt_str, errors='coerce')
                            else:
                                dt = pd.to_datetime(date, errors='coerce')
                        except:
                            dt = None
                    proc_list.append((code_clean, dt, i))
            return proc_list

        def parse_date_safe(date_input):
            """Safely parse various date formats"""
            if pd.isna(date_input) or date_input == '':
                return None
            try:
                return pd.to_datetime(date_input, errors='coerce')
            except:
                return None

        def check_timing_exclusions(proc_list, or_codes, treatment_codes, admission_date=None):
            """Advanced timing exclusion logic"""
            or_procs = [(code, dt, seq) for code, dt, seq in proc_list if code in or_codes]
            treatment_procs = [(code, dt, seq) for code, dt, seq in proc_list if code in treatment_codes]
            
            if not or_procs or not treatment_procs:
                return False, "Missing OR or treatment procedures"
            
            # Find earliest OR procedure
            or_with_dates = [(code, dt, seq) for code, dt, seq in or_procs if dt is not None]
            if or_with_dates:
                earliest_or = min(or_with_dates, key=lambda x: x[1])
                earliest_or_date = earliest_or[1]
                
                # Check if treatment occurs before OR
                treatment_with_dates = [(code, dt, seq) for code, dt, seq in treatment_procs if dt is not None]
                if treatment_with_dates:
                    earliest_treatment = min(treatment_with_dates, key=lambda x: x[1])
                    if earliest_treatment[1] <= earliest_or_date:
                        return True, f"Treatment procedure {earliest_treatment[0]} occurs before OR procedure"
            
            return False, "Timing validation passed"

        def check_psi14_timing_exclusions(proc_list, admit_date):
            """PSI 14 specific timing exclusions"""
            abdominal_open_codes = code_sets.get('ABDOMIPOPEN_CODES', [])
            abdominal_other_codes = code_sets.get('ABDOMIPOTHER_CODES', [])
            reclosure_codes = code_sets.get('RECLOIP_CODES', [])
            
            # Get procedure dates
            open_procs = [(code, dt, seq) for code, dt, seq in proc_list if code in abdominal_open_codes and dt is not None]
            other_procs = [(code, dt, seq) for code, dt, seq in proc_list if code in abdominal_other_codes and dt is not None]
            reclosure_procs = [(code, dt, seq) for code, dt, seq in proc_list if code in reclosure_codes and dt is not None]
            
            if not reclosure_procs:
                return False, "No reclosure procedures found"
            
            # Find earliest abdominal procedures and latest reclosure
            earliest_open = min(open_procs, key=lambda x: x[1])[1] if open_procs else None
            earliest_other = min(other_procs, key=lambda x: x[1])[1] if other_procs else None
            latest_reclosure = max(reclosure_procs, key=lambda x: x[1])[1] if reclosure_procs else None
            
            # Check if reclosure occurs before abdominal procedures
            exclude = False
            reason = ""
            
            if earliest_open and latest_reclosure <= earliest_open:
                exclude = True
                reason = "Reclosure occurs before or same day as open abdominal surgery"
            elif earliest_other and latest_reclosure <= earliest_other:
                exclude = True
                reason = "Reclosure occurs before or same day as other abdominal surgery"
            
            return exclude, reason

        def analyze_psi15_organ_injuries(dx_list, proc_list, admit_date, organ_systems):
            """Analyze organ-specific injuries for PSI 15"""
            results = {}
            
            # Find index abdominopelvic procedure date
            abdomi_codes = code_sets.get('ABDOMI15P_CODES', [])
            index_procs = [(code, dt, seq) for code, dt, seq in proc_list if code in abdomi_codes and dt is not None]
            
            if not index_procs:
                return results
            
            index_date = min(index_procs, key=lambda x: x[1])[1]
            
            # Analyze each organ system
            for organ_system in OrganSystem:
                organ_codes = organ_systems[organ_system]
                
                # Find injuries for this organ
                injuries = [(dx, poa, pos, seq) for dx, poa, pos, seq in dx_list 
                           if dx in organ_codes['injury_codes']]
                
                # Find related procedures in time window (1-30 days after index)
                related_procs_in_window = []
                for code, dt, seq in proc_list:
                    if code in organ_codes['procedure_codes'] and dt is not None:
                        days_diff = (dt - index_date).days
                        if 1 <= days_diff <= 30:
                            related_procs_in_window.append((code, dt, seq, days_diff))
                
                # Categorize injuries by POA status
                non_poa_injuries = [(dx, poa, pos, seq) for dx, poa, pos, seq in injuries 
                                   if pos == "SECONDARY" and poa != "Y"]
                poa_injuries = [(dx, poa, pos, seq) for dx, poa, pos, seq in injuries 
                               if pos == "PRINCIPAL" or poa == "Y"]
                
                results[organ_system] = {
                    'has_injury': len(injuries) > 0,
                    'has_non_poa_injury': len(non_poa_injuries) > 0,
                    'has_poa_injury': len(poa_injuries) > 0,
                    'has_related_procedure_in_window': len(related_procs_in_window) > 0,
                    'non_poa_injuries': non_poa_injuries,
                    'poa_injuries': poa_injuries,
                    'related_procedures': related_procs_in_window,
                    'meets_numerator_criteria': (len(non_poa_injuries) > 0 and len(related_procs_in_window) > 0)
                }
            
            return results

        def evaluate_psi_comprehensive(row, psi_name, code_sets, debug_mode=False):
            """Comprehensive PSI evaluation with detailed logic including PSI 13-15"""
            enc_id = row.get("EncounterID") or row.get("Encounter_ID") or "Unknown"
            age = row.get("Age", 0)
            ms_drg = str(row.get("MS-DRG", "")).strip()
            principal_dx = str(row.get("PrincipalDX", "")).replace(".", "").upper().strip()
            atype = row.get("ATYPE")
            mdc = row.get("MDC")
            drg = row.get("DRG")
            
            # Date fields
            admit_date = parse_date_safe(row.get("admission_date") or row.get("Admission_Date"))
            discharge_date = parse_date_safe(row.get("discharge_date") or row.get("Discharge_Date"))
            length_of_stay = row.get("length_of_stay") or row.get("Length_of_stay")
            
            dx_list = extract_dx_codes_enhanced(row)
            proc_list = extract_proc_info_enhanced(row)
            
            # Get principal and secondary diagnoses
            principal_diagnoses = [dx for dx, poa, pos, seq in dx_list if pos == "PRINCIPAL"]
            secondary_diagnoses = [dx for dx, poa, pos, seq in dx_list if pos == "SECONDARY"]
            
            psi_status = "Exclusion"
            rationale = []
            detailed_info = {}
            
            # Common exclusions first
            if age < 18:
                rationale.append(f"Age exclusion: {age} < 18")
                return psi_status, rationale, detailed_info
            
            if drg == 999:
                rationale.append("Ungroupable DRG (999)")
                return psi_status, rationale, detailed_info
                
            if principal_dx in code_sets.get("MDC14PRINDX_CODES", []):
                rationale.append("Obstetric case (MDC 14)")
                return psi_status, rationale, detailed_info
                
            if principal_dx in code_sets.get("MDC15PRINDX_CODES", []):
                rationale.append("Neonatal case (MDC 15)")
                return psi_status, rationale, detailed_info

            # PSI 13 - Postoperative Sepsis Rate
            if psi_name == "PSI_13":
                # Must be elective surgical
                if atype != 3:
                    rationale.append(f"Not elective admission: ATYPE = {atype} (required: 3)")
                    return psi_status, rationale, detailed_info
                
                if ms_drg not in code_sets.get("SURGI2R_CODES", []):
                    rationale.append("Not surgical DRG")
                    return psi_status, rationale, detailed_info
                
                # Must have OR procedure
                or_codes = code_sets.get("ORPROC_CODES", [])
                or_procs = [code for code, dt, seq in proc_list if code in or_codes]
                if not or_procs:
                    rationale.append("No operating room procedures found")
                    return psi_status, rationale, detailed_info
                
                # Sepsis exclusions
                sepsis_codes = code_sets.get("SEPTI2D_CODES", [])
                
                # Principal sepsis exclusion
                if principal_dx in sepsis_codes:
                    rationale.append("Principal diagnosis of sepsis")
                    return psi_status, rationale, detailed_info
                
                # POA sepsis exclusion
                poa_sepsis = [(dx, poa) for dx, poa, pos, seq in dx_list 
                             if pos == "SECONDARY" and dx in sepsis_codes and poa == "Y"]
                if poa_sepsis:
                    rationale.append(f"Sepsis present on admission: {poa_sepsis[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Infection exclusions
                infection_codes = code_sets.get("INFECID_CODES", [])
                
                # Principal infection exclusion
                if principal_dx in infection_codes:
                    rationale.append("Principal diagnosis of infection")
                    return psi_status, rationale, detailed_info
                
                # POA infection exclusion
                poa_infection = [(dx, poa) for dx, poa, pos, seq in dx_list 
                               if pos == "SECONDARY" and dx in infection_codes and poa == "Y"]
                if poa_infection:
                    rationale.append(f"Infection present on admission: {poa_infection[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Late surgery exclusion (≥10 days after admission)
                if admit_date:
                    or_with_dates = [(code, dt, seq) for code, dt, seq in proc_list 
                                    if code in or_codes and dt is not None]
                    if or_with_dates:
                        earliest_or = min(or_with_dates, key=lambda x: x[1])
                        days_to_surgery = (earliest_or[1] - admit_date).days
                        if days_to_surgery >= 10:
                            rationale.append(f"Late surgery: {days_to_surgery} days after admission (≥10)")
                            return psi_status, rationale, detailed_info
                
                # Check for postoperative sepsis
                postop_sepsis = [(dx, poa) for dx, poa, pos, seq in dx_list 
                               if pos == "SECONDARY" and dx in sepsis_codes and poa != "Y"]
                
                if postop_sepsis:
                    psi_status = "Inclusion"
                    rationale.append(f"Postoperative sepsis found: {postop_sepsis[0][0]} (POA: {postop_sepsis[0][1]})")
                    detailed_info["sepsis_matches"] = postop_sepsis
                else:
                    rationale.append("No qualifying postoperative sepsis codes found")

            # PSI 14 - Postoperative Wound Dehiscence Rate
            elif psi_name == "PSI_14":
                # Population inclusion - abdominopelvic surgery
                abdominal_open_codes = code_sets.get('ABDOMIPOPEN_CODES', [])
                abdominal_other_codes = code_sets.get('ABDOMIPOTHER_CODES', [])
                
                has_open_abdominal = any(code in abdominal_open_codes for code, dt, seq in proc_list)
                has_other_abdominal = any(code in abdominal_other_codes for code, dt, seq in proc_list)
                
                if not (has_open_abdominal or has_other_abdominal):
                    rationale.append("No abdominopelvic surgery procedures found")
                    return psi_status, rationale, detailed_info
                
                # Wound disruption codes
                wound_codes = code_sets.get('ABWALLCD_CODES', [])
                
                # Principal wound disruption exclusion
                if principal_dx in wound_codes:
                    rationale.append("Principal diagnosis of wound disruption")
                    return psi_status, rationale, detailed_info
                
                # POA wound disruption exclusion
                poa_wound = [(dx, poa) for dx, poa, pos, seq in dx_list 
                           if pos == "SECONDARY" and dx in wound_codes and poa == "Y"]
                if poa_wound:
                    rationale.append(f"Wound disruption present on admission: {poa_wound[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Length of stay exclusion (< 2 days)
                if pd.notna(length_of_stay) and length_of_stay < 2:
                    rationale.append(f"Length of stay < 2 days: {length_of_stay}")
                    return psi_status, rationale, detailed_info
                
                # Timing exclusions
                if validate_timing:
                    timing_exclude, timing_reason = check_psi14_timing_exclusions(proc_list, admit_date)
                    if timing_exclude:
                        rationale.append(f"Timing exclusion: {timing_reason}")
                        return psi_status, rationale, detailed_info
                
                # Dual numerator requirement: reclosure procedure AND wound disruption diagnosis
                reclosure_codes = code_sets.get('RECLOIP_CODES', [])
                
                has_reclosure = any(code in reclosure_codes for code, dt, seq in proc_list)
                wound_disruption_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                                          if dx in wound_codes and poa != "Y"]
                
                if has_reclosure and wound_disruption_matches:
                    psi_status = "Inclusion"
                    rationale.append("Both reclosure procedure and wound disruption diagnosis found")
                    detailed_info["has_reclosure"] = True
                    detailed_info["wound_matches"] = wound_disruption_matches
                    
                    # Determine stratum
                    if has_open_abdominal:
                        detailed_info["stratum"] = "open_approach"
                    else:
                        detailed_info["stratum"] = "non_open_approach"
                        
                elif has_reclosure:
                    rationale.append("Reclosure procedure found but no wound disruption diagnosis")
                elif wound_disruption_matches:
                    rationale.append("Wound disruption diagnosis found but no reclosure procedure")
                else:
                    rationale.append("Neither reclosure procedure nor wound disruption diagnosis found")

            # PSI 15 - Abdominopelvic Accidental Puncture or Laceration Rate
            elif psi_name == "PSI_15":
                # Population inclusion - surgical or medical with abdominopelvic procedure
                surgical_medical = (ms_drg in code_sets.get("SURGI2R_CODES", []) or 
                                  ms_drg in code_sets.get("MEDIC2R_CODES", []))
                if not surgical_medical:
                    rationale.append("Not surgical or medical DRG")
                    return psi_status, rationale, detailed_info
                
                # Must have abdominopelvic procedure
                abdomi_codes = code_sets.get('ABDOMI15P_CODES', [])
                abdomi_procs = [(code, dt, seq) for code, dt, seq in proc_list if code in abdomi_codes]
                if not abdomi_procs:
                    rationale.append("No abdominopelvic procedures found")
                    return psi_status, rationale, detailed_info
                
                # Check for missing procedure dates
                abdomi_with_dates = [(code, dt, seq) for code, dt, seq in abdomi_procs if dt is not None]
                if not abdomi_with_dates:
                    rationale.append("Missing abdominopelvic procedure dates")
                    return psi_status, rationale, detailed_info
                
                # Analyze organ-specific injuries
                organ_analysis = analyze_psi15_organ_injuries(dx_list, proc_list, admit_date, organ_systems)
                
                # Check for organ-specific POA exclusions
                poa_exclusions = []
                for organ_system, analysis in organ_analysis.items():
                    if analysis['has_poa_injury'] and analysis['has_related_procedure_in_window']:
                        poa_exclusions.append(organ_system.value)
                
                if poa_exclusions:
                    rationale.append(f"POA injury with related procedure for: {', '.join(poa_exclusions)}")
                    return psi_status, rationale, detailed_info
                
                # Check for numerator criteria (any organ system)
                qualifying_organs = []
                for organ_system, analysis in organ_analysis.items():
                    if analysis['meets_numerator_criteria']:
                        qualifying_organs.append(organ_system.value)
                
                if qualifying_organs:
                    psi_status = "Inclusion"
                    rationale.append(f"Organ injury with related procedure found: {', '.join(qualifying_organs)}")
                    detailed_info["qualifying_organs"] = qualifying_organs
                    detailed_info["organ_analysis"] = {
                        organ.value: analysis for organ, analysis in organ_analysis.items() 
                        if analysis['meets_numerator_criteria']
                    }
                else:
                    rationale.append("No organ-specific injury with related procedure within time window found")

            # Original PSI logic (05-12) remains the same...
            elif psi_name == "PSI_05":
                # Population inclusion
                if ms_drg not in code_sets.get("SURGI2R_CODES", []) and principal_dx not in code_sets.get("MDC14PRINDX_CODES", []):
                    rationale.append("Not surgical DRG or obstetric case")
                    return psi_status, rationale, detailed_info
                
                # Check for retained surgical items
                target_codes = code_sets.get("FOREIID_CODES", [])
                matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                          if pos == "SECONDARY" and dx in target_codes and poa != "Y