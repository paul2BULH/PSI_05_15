import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import json
import io
import logging
import os
import hashlib
import traceback
from enum import Enum
import uuid

# Configure logging
def setup_logging():
    """Setup comprehensive logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure main logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/psi_analyzer.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create specific loggers
    user_logger = logging.getLogger('user_activity')
    error_logger = logging.getLogger('errors')
    performance_logger = logging.getLogger('performance')
    
    # User activity logger
    user_handler = logging.FileHandler('logs/user_activity.log')
    user_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    user_logger.addHandler(user_handler)
    user_logger.setLevel(logging.INFO)
    
    # Error logger
    error_handler = logging.FileHandler('logs/errors.log')
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)
    
    # Performance logger
    perf_handler = logging.FileHandler('logs/performance.log')
    perf_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    performance_logger.addHandler(perf_handler)
    performance_logger.setLevel(logging.INFO)
    
    return user_logger, error_logger, performance_logger

# Initialize loggers
user_logger, error_logger, performance_logger = setup_logging()

def get_user_session_info():
    """Generate or retrieve user session information"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.session_start = datetime.now()
    
    # Try to get some user identification (be careful with privacy)
    user_ip = st.context.headers.get("x-forwarded-for", "unknown") if hasattr(st, 'context') else "unknown"
    user_agent = st.context.headers.get("user-agent", "unknown") if hasattr(st, 'context') else "unknown"
    
    return {
        'session_id': st.session_state.session_id,
        'session_start': st.session_state.session_start,
        'user_ip_hash': hashlib.md5(user_ip.encode()).hexdigest()[:8],  # Hash IP for privacy
        'user_agent_hash': hashlib.md5(user_agent.encode()).hexdigest()[:8]  # Hash user agent
    }

def log_user_activity(action, details=None, status="success"):
    """Log user activity with session information"""
    session_info = get_user_session_info()
    
    log_entry = {
        'session_id': session_info['session_id'],
        'user_ip_hash': session_info['user_ip_hash'],
        'user_agent_hash': session_info['user_agent_hash'],
        'action': action,
        'status': status,
        'details': details or {},
        'timestamp': datetime.now().isoformat()
    }
    
    user_logger.info(json.dumps(log_entry))

def log_error(error, context=None):
    """Log errors with full context"""
    session_info = get_user_session_info()
    
    error_entry = {
        'session_id': session_info['session_id'],
        'user_ip_hash': session_info['user_ip_hash'],
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {},
        'traceback': traceback.format_exc(),
        'timestamp': datetime.now().isoformat()
    }
    
    error_logger.error(json.dumps(error_entry))

def log_performance(action, duration_seconds, details=None):
    """Log performance metrics"""
    session_info = get_user_session_info()
    
    perf_entry = {
        'session_id': session_info['session_id'],
        'action': action,
        'duration_seconds': duration_seconds,
        'details': details or {},
        'timestamp': datetime.now().isoformat()
    }
    
    performance_logger.info(json.dumps(perf_entry))

def log_psi_results(psi_name, total_cases, inclusions, exclusions, rate):
    """Log PSI analysis results"""
    results = {
        'psi': psi_name,
        'total_cases': total_cases,
        'inclusions': inclusions,
        'exclusions': exclusions,
        'rate_per_1000': rate,
        'inclusion_percentage': (inclusions/total_cases*100) if total_cases > 0 else 0
    }
    
    log_user_activity('psi_analysis_completed', results)

# Streamlit page configuration
st.set_page_config(page_title="Enhanced PSI Web Debugger (PSI 05-15)", layout="wide")

# Log page load
log_user_activity('page_loaded', {'page': 'PSI Analyzer'})

st.title("🏥 Enhanced PSI 05–15 Analyzer + Debugger")
st.markdown("*Comprehensive Patient Safety Indicator Analysis with Advanced Logic*")

# Display session information in sidebar (for debugging)
with st.sidebar:
    st.header("🔧 Configuration")
    debug_mode = st.checkbox("Enable Debug Mode", value=True)
    show_exclusions = st.checkbox("Show Detailed Exclusions", value=True)
    validate_timing = st.checkbox("Enable Timing Validation", value=True)
    
    # Log configuration changes
    if st.button("Log Current Settings"):
        config = {
            'debug_mode': debug_mode,
            'show_exclusions': show_exclusions,
            'validate_timing': validate_timing
        }
        log_user_activity('configuration_updated', config)
        st.success("Settings logged!")
    
    st.header("🎯 PSI Selection")
    selected_psis = st.multiselect(
        "Select PSIs to Analyze",
        ["PSI_05", "PSI_06", "PSI_07", "PSI_08", "PSI_09", "PSI_10", "PSI_11", "PSI_12", "PSI_13", "PSI_14", "PSI_15"],
        default=["PSI_13", "PSI_14", "PSI_15"]
    )
    
    # Log PSI selection
    if selected_psis:
        log_user_activity('psi_selection', {'selected_psis': selected_psis})
    
    # Session info (for admin/debugging)
    if debug_mode:
        st.header("🔍 Session Info")
        session_info = get_user_session_info()
        st.text(f"Session: {session_info['session_id'][:8]}...")
        st.text(f"Started: {session_info['session_start'].strftime('%H:%M:%S')}")
        
        # Display recent logs button
        if st.button("Show Recent Activity"):
            try:
                with open('logs/user_activity.log', 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-10:]  # Last 10 entries
                    st.text_area("Recent Activity", "\n".join(recent_lines), height=200)
            except FileNotFoundError:
                st.info("No activity log file found")

# File upload section
col1, col2 = st.columns(2)
with col1:
    input_file = st.file_uploader("📁 Upload PSI Input Excel", type=[".xlsx"])
with col2:
    appendix_file = st.file_uploader("📋 Upload PSI Appendix Excel", type=[".xlsx"])

# Log file uploads
if input_file:
    file_info = {
        'filename': input_file.name,
        'size_bytes': input_file.size,
        'type': 'input_file'
    }
    log_user_activity('file_uploaded', file_info)

if appendix_file:
    file_info = {
        'filename': appendix_file.name,
        'size_bytes': appendix_file.size,
        'type': 'appendix_file'
    }
    log_user_activity('file_uploaded', file_info)

if input_file and appendix_file:
    start_time = datetime.now()
    
    try:
        # Load data with progress bar
        with st.spinner("Loading and processing data..."):
            load_start = datetime.now()
            df_input = pd.read_excel(input_file)
            appendix_df = pd.read_excel(appendix_file)
            load_duration = (datetime.now() - load_start).total_seconds()
            
            # Log data loading performance
            load_details = {
                'input_rows': len(df_input),
                'input_columns': len(df_input.columns),
                'appendix_rows': len(appendix_df),
                'appendix_columns': len(appendix_df.columns)
            }
            log_performance('data_loading', load_duration, load_details)
            log_user_activity('data_loaded', load_details)

        # Extract and organize code sets (enhanced for PSI 13-15)
        code_processing_start = datetime.now()
        
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

        code_processing_duration = (datetime.now() - code_processing_start).total_seconds()
        
        # Log code set processing
        code_set_details = {
            'total_code_sets': len(code_sets),
            'total_codes': sum(len(codes) for codes in code_sets.values())
        }
        log_performance('code_processing', code_processing_duration, code_set_details)

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

            # PSI 05 - Foreign Object Retained After Surgery
            if psi_name == "PSI_05":
                # Population inclusion
                if ms_drg not in code_sets.get("SURGI2R_CODES", []) and principal_dx not in code_sets.get("MDC14PRINDX_CODES", []):
                    rationale.append("Not surgical DRG or obstetric case")
                    return psi_status, rationale, detailed_info
                
                # Check for retained surgical items
                target_codes = code_sets.get("FOREIID_CODES", [])
                matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                          if pos == "SECONDARY" and dx in target_codes and poa != "Y"]
                
                if matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Foreign object retained after surgery: {matches[0][0]}")
                    detailed_info["foreign_object_matches"] = matches
                else:
                    rationale.append("No qualifying foreign object codes found")

            # PSI 06 - Iatrogenic Pneumothorax Rate
            elif psi_name == "PSI_06":
                # Population inclusion - surgical or medical
                if ms_drg not in code_sets.get("SURGI2R_CODES", []) and ms_drg not in code_sets.get("MEDIC2R_CODES", []):
                    rationale.append("Not surgical or medical DRG")
                    return psi_status, rationale, detailed_info
                
                # Exclusions
                iatrogenic_codes = code_sets.get("IATROID_CODES", [])
                traumatic_codes = code_sets.get("CTRAUMD_CODES", [])
                pleural_codes = code_sets.get("PLEURAD_CODES", [])
                
                # Check exclusion conditions
                if principal_dx in iatrogenic_codes:
                    rationale.append("Principal diagnosis of iatrogenic pneumothorax")
                    return psi_status, rationale, detailed_info
                
                if principal_dx in traumatic_codes:
                    rationale.append("Principal diagnosis of chest trauma")
                    return psi_status, rationale, detailed_info
                
                if principal_dx in pleural_codes:
                    rationale.append("Principal diagnosis of pleural effusion/empyema")
                    return psi_status, rationale, detailed_info
                
                # POA exclusions
                poa_iatrogenic = [(dx, poa) for dx, poa, pos, seq in dx_list 
                                if pos == "SECONDARY" and dx in iatrogenic_codes and poa == "Y"]
                if poa_iatrogenic:
                    rationale.append(f"Iatrogenic pneumothorax present on admission: {poa_iatrogenic[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Check for iatrogenic pneumothorax procedure
                iat_ptx_codes = code_sets.get("IATPTXD_CODES", [])
                ptx_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                             if pos == "SECONDARY" and dx in iat_ptx_codes and poa != "Y"]
                
                if ptx_matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Iatrogenic pneumothorax found: {ptx_matches[0][0]}")
                    detailed_info["pneumothorax_matches"] = ptx_matches
                else:
                    rationale.append("No qualifying iatrogenic pneumothorax codes found")

            # PSI 07 - Central Venous Catheter-Related Blood Stream Infection Rate
            elif psi_name == "PSI_07":
                # Population inclusion - surgical or medical
                if ms_drg not in code_sets.get("SURGI2R_CODES", []) and ms_drg not in code_sets.get("MEDIC2R_CODES", []):
                    rationale.append("Not surgical or medical DRG")
                    return psi_status, rationale, detailed_info
                
                # Exclusions
                infection_codes = code_sets.get("IDTMC3D_CODES", [])
                cancer_codes = code_sets.get("CANCEID_CODES", [])
                immune_codes = code_sets.get("IMMUNID_CODES", [])
                
                # Check exclusions
                if principal_dx in infection_codes:
                    rationale.append("Principal diagnosis of infection")
                    return psi_status, rationale, detailed_info
                
                if principal_dx in cancer_codes:
                    rationale.append("Principal diagnosis of cancer")
                    return psi_status, rationale, detailed_info
                
                if principal_dx in immune_codes:
                    rationale.append("Principal diagnosis of immunocompromised state")
                    return psi_status, rationale, detailed_info
                
                # POA infection exclusion
                poa_infection = [(dx, poa) for dx, poa, pos, seq in dx_list 
                               if pos == "SECONDARY" and dx in infection_codes and poa == "Y"]
                if poa_infection:
                    rationale.append(f"Infection present on admission: {poa_infection[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Check for central line infection
                cvc_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                             if pos == "SECONDARY" and dx in infection_codes and poa != "Y"]
                
                if cvc_matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Central venous catheter infection found: {cvc_matches[0][0]}")
                    detailed_info["cvc_infection_matches"] = cvc_matches
                else:
                    rationale.append("No qualifying central venous catheter infection codes found")

            # PSI 08 - In-Hospital Fall with Hip Fracture Rate
            elif psi_name == "PSI_08":
                # Population inclusion - all discharges (no specific DRG requirements)
                
                # Exclusions
                fx_codes = code_sets.get("FXID_CODES", [])
                hip_fx_codes = code_sets.get("HIPFXID_CODES", [])
                prosthetic_fx_codes = code_sets.get("PROSFXID_CODES", [])
                
                # Principal hip fracture exclusion
                if principal_dx in hip_fx_codes:
                    rationale.append("Principal diagnosis of hip fracture")
                    return psi_status, rationale, detailed_info
                
                # Principal prosthetic fracture exclusion
                if principal_dx in prosthetic_fx_codes:
                    rationale.append("Principal diagnosis of prosthetic fracture")
                    return psi_status, rationale, detailed_info
                
                # POA hip fracture exclusion
                poa_fx = [(dx, poa) for dx, poa, pos, seq in dx_list 
                         if pos == "SECONDARY" and dx in hip_fx_codes and poa == "Y"]
                if poa_fx:
                    rationale.append(f"Hip fracture present on admission: {poa_fx[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Check for in-hospital hip fracture
                hip_fx_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                                if pos == "SECONDARY" and dx in hip_fx_codes and poa != "Y"]
                
                if hip_fx_matches:
                    psi_status = "Inclusion"
                    rationale.append(f"In-hospital hip fracture found: {hip_fx_matches[0][0]}")
                    detailed_info["hip_fracture_matches"] = hip_fx_matches
                else:
                    rationale.append("No qualifying in-hospital hip fracture codes found")

            # PSI 09 - Perioperative Hemorrhage or Hematoma Rate
            elif psi_name == "PSI_09":
                # Population inclusion - surgical DRG
                if ms_drg not in code_sets.get("SURGI2R_CODES", []):
                    rationale.append("Not surgical DRG")
                    return psi_status, rationale, detailed_info
                
                # Exclusions
                hemorrhage_codes = code_sets.get("POHMRI2D_CODES", [])
                hematoma_codes = code_sets.get("HEMOTH2P_CODES", [])
                coag_codes = code_sets.get("COAGDID_CODES", [])
                bleeding_codes = code_sets.get("MEDBLEEDD_CODES", [])
                
                # Principal hemorrhage/hematoma exclusion
                if principal_dx in hemorrhage_codes or principal_dx in hematoma_codes:
                    rationale.append("Principal diagnosis of hemorrhage or hematoma")
                    return psi_status, rationale, detailed_info
                
                # Coagulopathy exclusions
                if principal_dx in coag_codes:
                    rationale.append("Principal diagnosis of coagulopathy")
                    return psi_status, rationale, detailed_info
                
                # POA coagulopathy exclusion
                poa_coag = [(dx, poa) for dx, poa, pos, seq in dx_list 
                           if pos == "SECONDARY" and dx in coag_codes and poa == "Y"]
                if poa_coag:
                    rationale.append(f"Coagulopathy present on admission: {poa_coag[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Medical bleeding disorder exclusions
                if principal_dx in bleeding_codes:
                    rationale.append("Principal diagnosis of bleeding disorder")
                    return psi_status, rationale, detailed_info
                
                poa_bleeding = [(dx, poa) for dx, poa, pos, seq in dx_list 
                              if pos == "SECONDARY" and dx in bleeding_codes and poa == "Y"]
                if poa_bleeding:
                    rationale.append(f"Bleeding disorder present on admission: {poa_bleeding[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # POA hemorrhage/hematoma exclusion
                poa_hem = [(dx, poa) for dx, poa, pos, seq in dx_list 
                          if pos == "SECONDARY" and (dx in hemorrhage_codes or dx in hematoma_codes) and poa == "Y"]
                if poa_hem:
                    rationale.append(f"Hemorrhage/hematoma present on admission: {poa_hem[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Check for perioperative hemorrhage or hematoma
                hem_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                             if pos == "SECONDARY" and (dx in hemorrhage_codes or dx in hematoma_codes) and poa != "Y"]
                
                if hem_matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Perioperative hemorrhage/hematoma found: {hem_matches[0][0]}")
                    detailed_info["hemorrhage_matches"] = hem_matches
                else:
                    rationale.append("No qualifying perioperative hemorrhage/hematoma codes found")

            # PSI 10 - Postoperative Acute Kidney Injury Requiring Dialysis Rate
            elif psi_name == "PSI_10":
                # Population inclusion - surgical DRG
                if ms_drg not in code_sets.get("SURGI2R_CODES", []):
                    rationale.append("Not surgical DRG")
                    return psi_status, rationale, detailed_info
                
                # Exclusions
                physio_codes = code_sets.get("PHYSIDB_CODES", [])
                dialysis_codes = code_sets.get("DIALYIP_CODES", [])
                cardiac_codes = code_sets.get("CARDIID_CODES", [])
                cardio_resp_codes = code_sets.get("CARDRID_CODES", [])
                shock_codes = code_sets.get("SHOCKID_CODES", [])
                renal_failure_codes = code_sets.get("CRENLFD_CODES", [])
                
                # Principal renal failure exclusion
                if principal_dx in renal_failure_codes:
                    rationale.append("Principal diagnosis of chronic renal failure")
                    return psi_status, rationale, detailed_info
                
                # Principal cardiac exclusions
                if principal_dx in cardiac_codes:
                    rationale.append("Principal diagnosis of cardiac condition")
                    return psi_status, rationale, detailed_info
                
                if principal_dx in cardio_resp_codes:
                    rationale.append("Principal diagnosis of cardiorespiratory failure")
                    return psi_status, rationale, detailed_info
                
                if principal_dx in shock_codes:
                    rationale.append("Principal diagnosis of shock")
                    return psi_status, rationale, detailed_info
                
                # POA exclusions
                poa_renal = [(dx, poa) for dx, poa, pos, seq in dx_list 
                           if pos == "SECONDARY" and dx in renal_failure_codes and poa == "Y"]
                if poa_renal:
                    rationale.append(f"Chronic renal failure present on admission: {poa_renal[0][0]}")
                    return psi_status, rationale, detailed_info
                
                poa_physio = [(dx, poa) for dx, poa, pos, seq in dx_list 
                            if pos == "SECONDARY" and dx in physio_codes and poa == "Y"]
                if poa_physio:
                    rationale.append(f"Physiologic kidney condition present on admission: {poa_physio[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Check for acute kidney injury requiring dialysis
                # Must have both acute kidney injury and dialysis procedure
                aki_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                             if pos == "SECONDARY" and dx in physio_codes and poa != "Y"]
                
                dialysis_procs = [code for code, dt, seq in proc_list if code in dialysis_codes]
                
                if aki_matches and dialysis_procs:
                    psi_status = "Inclusion"
                    rationale.append(f"Acute kidney injury with dialysis found: {aki_matches[0][0]}")
                    detailed_info["aki_matches"] = aki_matches
                    detailed_info["dialysis_procedures"] = dialysis_procs
                elif aki_matches:
                    rationale.append("Acute kidney injury found but no dialysis procedure")
                elif dialysis_procs:
                    rationale.append("Dialysis procedure found but no acute kidney injury")
                else:
                    rationale.append("No qualifying acute kidney injury or dialysis procedure found")

            # PSI 11 - Postoperative Respiratory Failure Rate
            elif psi_name == "PSI_11":
                # Population inclusion - surgical DRG
                if ms_drg not in code_sets.get("SURGI2R_CODES", []):
                    rationale.append("Not surgical DRG")
                    return psi_status, rationale, detailed_info
                
                # Exclusions
                acute_rf_codes = code_sets.get("ACURF2D_CODES", [])
                chronic_rf_codes = code_sets.get("ACURF3D_CODES", [])
                neuro_codes = code_sets.get("NEUROMD_CODES", [])
                malnutrition_codes = code_sets.get("MALHYPD_CODES", [])
                
                # Procedure codes
                trach_codes = code_sets.get("PR9672P_CODES", [])
                reintub_codes = code_sets.get("PR9671P_CODES", [])
                ventilator_codes = code_sets.get("PR9604P_CODES", [])
                
                # Principal respiratory failure exclusion
                if principal_dx in acute_rf_codes or principal_dx in chronic_rf_codes:
                    rationale.append("Principal diagnosis of respiratory failure")
                    return psi_status, rationale, detailed_info
                
                # Principal neuromuscular exclusion
                if principal_dx in neuro_codes:
                    rationale.append("Principal diagnosis of neuromuscular disorder")
                    return psi_status, rationale, detailed_info
                
                # Principal malnutrition exclusion
                if principal_dx in malnutrition_codes:
                    rationale.append("Principal diagnosis of malnutrition")
                    return psi_status, rationale, detailed_info
                
                # POA exclusions
                poa_rf = [(dx, poa) for dx, poa, pos, seq in dx_list 
                         if pos == "SECONDARY" and (dx in acute_rf_codes or dx in chronic_rf_codes) and poa == "Y"]
                if poa_rf:
                    rationale.append(f"Respiratory failure present on admission: {poa_rf[0][0]}")
                    return psi_status, rationale, detailed_info
                
                poa_neuro = [(dx, poa) for dx, poa, pos, seq in dx_list 
                           if pos == "SECONDARY" and dx in neuro_codes and poa == "Y"]
                if poa_neuro:
                    rationale.append(f"Neuromuscular disorder present on admission: {poa_neuro[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Check for postoperative respiratory failure
                # Must have respiratory failure diagnosis AND qualifying procedure
                rf_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                            if pos == "SECONDARY" and dx in acute_rf_codes and poa != "Y"]
                
                qualifying_procs = [code for code, dt, seq in proc_list 
                                  if code in trach_codes or code in reintub_codes or code in ventilator_codes]
                
                if rf_matches and qualifying_procs:
                    psi_status = "Inclusion"
                    rationale.append(f"Postoperative respiratory failure found: {rf_matches[0][0]}")
                    detailed_info["respiratory_failure_matches"] = rf_matches
                    detailed_info["respiratory_procedures"] = qualifying_procs
                elif rf_matches:
                    rationale.append("Respiratory failure found but no qualifying procedure")
                elif qualifying_procs:
                    rationale.append("Qualifying respiratory procedure found but no respiratory failure diagnosis")
                else:
                    rationale.append("No qualifying postoperative respiratory failure found")

            # PSI 12 - Perioperative Pulmonary Embolism or Deep Vein Thrombosis Rate
            elif psi_name == "PSI_12":
                # Population inclusion - surgical or medical DRG
                if ms_drg not in code_sets.get("SURGI2R_CODES", []) and ms_drg not in code_sets.get("MEDIC2R_CODES", []):
                    rationale.append("Not surgical or medical DRG")
                    return psi_status, rationale, detailed_info
                
                # Exclusions
                dvt_codes = code_sets.get("DEEPVIB_CODES", [])
                pe_codes = code_sets.get("PULMOID_CODES", [])
                hit_codes = code_sets.get("HITD_CODES", [])
                neutrauma_codes = code_sets.get("NEURTRAD_CODES", [])
                
                # Principal DVT/PE exclusion
                if principal_dx in dvt_codes or principal_dx in pe_codes:
                    rationale.append("Principal diagnosis of DVT or PE")
                    return psi_status, rationale, detailed_info
                
                # Principal trauma exclusions
                if principal_dx in hit_codes:
                    rationale.append("Principal diagnosis of trauma with injury to lower extremity")
                    return psi_status, rationale, detailed_info
                
                if principal_dx in neutrauma_codes:
                    rationale.append("Principal diagnosis of neurologic trauma")
                    return psi_status, rationale, detailed_info
                
                # POA exclusions
                poa_dvt_pe = [(dx, poa) for dx, poa, pos, seq in dx_list 
                            if pos == "SECONDARY" and (dx in dvt_codes or dx in pe_codes) and poa == "Y"]
                if poa_dvt_pe:
                    rationale.append(f"DVT/PE present on admission: {poa_dvt_pe[0][0]}")
                    return psi_status, rationale, detailed_info
                
                poa_trauma = [(dx, poa) for dx, poa, pos, seq in dx_list 
                            if pos == "SECONDARY" and (dx in hit_codes or dx in neutrauma_codes) and poa == "Y"]
                if poa_trauma:
                    rationale.append(f"Trauma present on admission: {poa_trauma[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Check for perioperative DVT or PE
                dvt_pe_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                                if pos == "SECONDARY" and (dx in dvt_codes or dx in pe_codes) and poa != "Y"]
                
                if dvt_pe_matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Perioperative DVT/PE found: {dvt_pe_matches[0][0]}")
                    detailed_info["dvt_pe_matches"] = dvt_pe_matches
                else:
                    rationale.append("No qualifying perioperative DVT/PE codes found")

            # PSI 13 - Postoperative Sepsis Rate
            elif psi_name == "PSI_13":
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
            
            else:
                rationale.append(f"PSI {psi_name} logic not yet implemented")

            return psi_status, rationale, detailed_info

        # Main analysis
        if selected_psis:
            # Log analysis start
            analysis_start_time = datetime.now()
            analysis_details = {
                'selected_psis': selected_psis,
                'total_cases': len(df_input),
                'debug_mode': debug_mode,
                'validate_timing': validate_timing
            }
            log_user_activity('analysis_started', analysis_details)
            
            results = []
            
            for psi in selected_psis:
                psi_start_time = datetime.now()
                
                st.subheader(f"📊 {psi} Analysis Results")
                
                # Create columns for metrics
                col1, col2, col3, col4 = st.columns(4)
                
                # Initialize counters
                inclusions = 0
                exclusions = 0
                total_cases = len(df_input)
                
                # Detailed results storage
                detailed_results = []
                
                # Process each row
                progress_bar = st.progress(0)
                processing_errors = 0
                
                for idx, row in df_input.iterrows():
                    progress_bar.progress((idx + 1) / total_cases)
                    
                    try:
                        status, rationale, detailed_info = evaluate_psi_comprehensive(
                            row, psi, code_sets, debug_mode=debug_mode
                        )
                        
                        if status == "Inclusion":
                            inclusions += 1
                        else:
                            exclusions += 1
                        
                        # Store detailed results
                        result_record = {
                            "EncounterID": row.get("EncounterID") or row.get("Encounter_ID") or f"Row_{idx}",
                            "Status": status,
                            "Rationale": "; ".join(rationale),
                            "Age": row.get("Age", ""),
                            "MS_DRG": row.get("MS-DRG", ""),
                            "PrincipalDX": row.get("PrincipalDX", ""),
                            "ATYPE": row.get("ATYPE", ""),
                            "Length_of_Stay": row.get("length_of_stay") or row.get("Length_of_stay", "")
                        }
                        
                        # Add PSI-specific details
                        if detailed_info:
                            for key, value in detailed_info.items():
                                result_record[f"Detail_{key}"] = str(value)
                        
                        detailed_results.append(result_record)
                        
                    except Exception as e:
                        processing_errors += 1
                        error_context = {
                            'psi': psi,
                            'row_index': idx,
                            'encounter_id': row.get("EncounterID") or row.get("Encounter_ID") or f"Row_{idx}"
                        }
                        log_error(e, error_context)
                        
                        # Create error result record
                        result_record = {
                            "EncounterID": row.get("EncounterID") or row.get("Encounter_ID") or f"Row_{idx}",
                            "Status": "Error",
                            "Rationale": f"Processing error: {str(e)}",
                            "Age": row.get("Age", ""),
                            "MS_DRG": row.get("MS-DRG", ""),
                            "PrincipalDX": row.get("PrincipalDX", ""),
                            "ATYPE": row.get("ATYPE", ""),
                            "Length_of_Stay": row.get("length_of_stay") or row.get("Length_of_stay", "")
                        }
                        detailed_results.append(result_record)
                
                progress_bar.empty()
                
                # Calculate PSI processing time
                psi_duration = (datetime.now() - psi_start_time).total_seconds()
                
                # Display metrics
                with col1:
                    st.metric("Total Cases", total_cases)
                with col2:
                    inclusion_pct = (inclusions/total_cases*100) if total_cases > 0 else 0
                    st.metric("Inclusions", inclusions, delta=f"{inclusion_pct:.1f}%")
                with col3:
                    exclusion_pct = (exclusions/total_cases*100) if total_cases > 0 else 0
                    st.metric("Exclusions", exclusions, delta=f"{exclusion_pct:.1f}%")
                with col4:
                    rate = (inclusions / total_cases * 1000) if total_cases > 0 else 0
                    st.metric("Rate per 1000", f"{rate:.2f}")
                
                # Log PSI results
                log_psi_results(psi, total_cases, inclusions, exclusions, rate)
                
                # Log performance metrics
                psi_perf_details = {
                    'total_cases': total_cases,
                    'inclusions': inclusions,
                    'exclusions': exclusions,
                    'processing_errors': processing_errors,
                    'rate_per_1000': rate
                }
                log_performance(f'psi_{psi}_analysis', psi_duration, psi_perf_details)
                
                # Show processing errors if any
                if processing_errors > 0:
                    st.warning(f"⚠️ {processing_errors} processing errors occurred during {psi} analysis. Check error logs for details.")
                
                # Results DataFrame
                results_df = pd.DataFrame(detailed_results)
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.selectbox(f"Filter by Status ({psi})", 
                                               ["All", "Inclusion", "Exclusion", "Error"], 
                                               key=f"status_{psi}")
                with col2:
                    show_details = st.checkbox(f"Show Detailed Columns ({psi})", 
                                             value=False, key=f"details_{psi}")
                
                # Apply filters
                filtered_df = results_df.copy()
                if status_filter != "All":
                    filtered_df = filtered_df[filtered_df["Status"] == status_filter]
                
                # Select columns to display
                if show_details:
                    display_cols = list(filtered_df.columns)
                else:
                    display_cols = ["EncounterID", "Status", "Rationale", "Age", "MS_DRG", "PrincipalDX"]
                    display_cols = [col for col in display_cols if col in filtered_df.columns]
                
                # Display results table
                st.dataframe(
                    filtered_df[display_cols],
                    use_container_width=True,
                    height=400
                )
                
                # Download options
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = filtered_df.to_csv(index=False)
                    download_time = datetime.now()
                    if st.download_button(
                        f"📥 Download {psi} Results (CSV)",
                        csv_data,
                        f"{psi}_results.csv",
                        "text/csv"
                    ):
                        log_user_activity('file_downloaded', {
                            'psi': psi,
                            'format': 'csv',
                            'filtered_rows': len(filtered_df),
                            'total_rows': len(results_df)
                        })
                
                with col2:
                    # Create Excel buffer
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        filtered_df.to_excel(writer, sheet_name=f'{psi}_Results', index=False)
                    excel_data = excel_buffer.getvalue()
                    
                    if st.download_button(
                        f"📥 Download {psi} Results (Excel)",
                        excel_data,
                        f"{psi}_results.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ):
                        log_user_activity('file_downloaded', {
                            'psi': psi,
                            'format': 'excel',
                            'filtered_rows': len(filtered_df),
                            'total_rows': len(results_df)
                        })
                
                # Debug information
                if debug_mode:
                    with st.expander(f"🔍 Debug Information for {psi}"):
                        st.write("**Code Sets Used:**")
                        relevant_codes = {}
                        
                        if psi == "PSI_05":
                            relevant_codes = {
                                "FOREIID_CODES": len(code_sets.get("FOREIID_CODES", [])),
                                "SURGI2R_CODES": len(code_sets.get("SURGI2R_CODES", [])),
                                "MDC14PRINDX_CODES": len(code_sets.get("MDC14PRINDX_CODES", []))
                            }
                        elif psi == "PSI_06":
                            relevant_codes = {
                                "IATROID_CODES": len(code_sets.get("IATROID_CODES", [])),
                                "IATPTXD_CODES": len(code_sets.get("IATPTXD_CODES", [])),
                                "CTRAUMD_CODES": len(code_sets.get("CTRAUMD_CODES", [])),
                                "PLEURAD_CODES": len(code_sets.get("PLEURAD_CODES", [])),
                                "SURGI2R_CODES": len(code_sets.get("SURGI2R_CODES", [])),
                                "MEDIC2R_CODES": len(code_sets.get("MEDIC2R_CODES", []))
                            }
                        elif psi == "PSI_07":
                            relevant_codes = {
                                "IDTMC3D_CODES": len(code_sets.get("IDTMC3D_CODES", [])),
                                "CANCEID_CODES": len(code_sets.get("CANCEID_CODES", [])),
                                "IMMUNID_CODES": len(code_sets.get("IMMUNID_CODES", [])),
                                "SURGI2R_CODES": len(code_sets.get("SURGI2R_CODES", [])),
                                "MEDIC2R_CODES": len(code_sets.get("MEDIC2R_CODES", []))
                            }
                        elif psi == "PSI_08":
                            relevant_codes = {
                                "FXID_CODES": len(code_sets.get("FXID_CODES", [])),
                                "HIPFXID_CODES": len(code_sets.get("HIPFXID_CODES", [])),
                                "PROSFXID_CODES": len(code_sets.get("PROSFXID_CODES", []))
                            }
                        elif psi == "PSI_09":
                            relevant_codes = {
                                "POHMRI2D_CODES": len(code_sets.get("POHMRI2D_CODES", [])),
                                "HEMOTH2P_CODES": len(code_sets.get("HEMOTH2P_CODES", [])),
                                "COAGDID_CODES": len(code_sets.get("COAGDID_CODES", [])),
                                "MEDBLEEDD_CODES": len(code_sets.get("MEDBLEEDD_CODES", [])),
                                "SURGI2R_CODES": len(code_sets.get("SURGI2R_CODES", []))
                            }
                        elif psi == "PSI_10":
                            relevant_codes = {
                                "PHYSIDB_CODES": len(code_sets.get("PHYSIDB_CODES", [])),
                                "DIALYIP_CODES": len(code_sets.get("DIALYIP_CODES", [])),
                                "CARDIID_CODES": len(code_sets.get("CARDIID_CODES", [])),
                                "CARDRID_CODES": len(code_sets.get("CARDRID_CODES", [])),
                                "SHOCKID_CODES": len(code_sets.get("SHOCKID_CODES", [])),
                                "CRENLFD_CODES": len(code_sets.get("CRENLFD_CODES", [])),
                                "SURGI2R_CODES": len(code_sets.get("SURGI2R_CODES", []))
                            }
                        elif psi == "PSI_11":
                            relevant_codes = {
                                "ACURF2D_CODES": len(code_sets.get("ACURF2D_CODES", [])),
                                "ACURF3D_CODES": len(code_sets.get("ACURF3D_CODES", [])),
                                "PR9672P_CODES": len(code_sets.get("PR9672P_CODES", [])),
                                "PR9671P_CODES": len(code_sets.get("PR9671P_CODES", [])),
                                "PR9604P_CODES": len(code_sets.get("PR9604P_CODES", [])),
                                "NEUROMD_CODES": len(code_sets.get("NEUROMD_CODES", [])),
                                "MALHYPD_CODES": len(code_sets.get("MALHYPD_CODES", [])),
                                "SURGI2R_CODES": len(code_sets.get("SURGI2R_CODES", []))
                            }
                        elif psi == "PSI_12":
                            relevant_codes = {
                                "DEEPVIB_CODES": len(code_sets.get("DEEPVIB_CODES", [])),
                                "PULMOID_CODES": len(code_sets.get("PULMOID_CODES", [])),
                                "HITD_CODES": len(code_sets.get("HITD_CODES", [])),
                                "NEURTRAD_CODES": len(code_sets.get("NEURTRAD_CODES", [])),
                                "SURGI2R_CODES": len(code_sets.get("SURGI2R_CODES", [])),
                                "MEDIC2R_CODES": len(code_sets.get("MEDIC2R_CODES", []))
                            }
                        elif psi == "PSI_13":
                            relevant_codes = {
                                "SEPTI2D_CODES": len(code_sets.get("SEPTI2D_CODES", [])),
                                "INFECID_CODES": len(code_sets.get("INFECID_CODES", [])),
                                "ORPROC_CODES": len(code_sets.get("ORPROC_CODES", [])),
                                "SURGI2R_CODES": len(code_sets.get("SURGI2R_CODES", []))
                            }
                        elif psi == "PSI_14":
                            relevant_codes = {
                                "ABDOMIPOPEN_CODES": len(code_sets.get("ABDOMIPOPEN_CODES", [])),
                                "ABDOMIPOTHER_CODES": len(code_sets.get("ABDOMIPOTHER_CODES", [])),
                                "RECLOIP_CODES": len(code_sets.get("RECLOIP_CODES", [])),
                                "ABWALLCD_CODES": len(code_sets.get("ABWALLCD_CODES", []))
                            }
                        elif psi == "PSI_15":
                            relevant_codes = {
                                "ABDOMI15P_CODES": len(code_sets.get("ABDOMI15P_CODES", [])),
                                "SPLEEN15D_CODES": len(code_sets.get("SPLEEN15D_CODES", [])),
                                "VESSEL15D_CODES": len(code_sets.get("VESSEL15D_CODES", [])),
                                "GI15D_CODES": len(code_sets.get("GI15D_CODES", [])),
                                "GU15D_CODES": len(code_sets.get("GU15D_CODES", [])),
                                "ADRENAL15D_CODES": len(code_sets.get("ADRENAL15D_CODES", [])),
                                "DIAPHR15D_CODES": len(code_sets.get("DIAPHR15D_CODES", []))
                            }
                        
                        for code_type, count in relevant_codes.items():
                            st.write(f"- {code_type}: {count} codes")
                        
                        # Processing statistics
                        st.write("**Processing Statistics:**")
                        st.write(f"- Processing time: {psi_duration:.2f} seconds")
                        st.write(f"- Processing errors: {processing_errors}")
                        st.write(f"- Cases per second: {total_cases/psi_duration:.1f}")
                
                # Summary statistics
                with st.expander(f"📈 Summary Statistics for {psi}"):
                    st.write("**Inclusion/Exclusion Breakdown:**")
                    status_counts = filtered_df['Status'].value_counts()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if 'Inclusion' in status_counts:
                            st.metric("Inclusions", status_counts['Inclusion'])
                        else:
                            st.metric("Inclusions", 0)
                    with col2:
                        if 'Exclusion' in status_counts:
                            st.metric("Exclusions", status_counts['Exclusion'])
                        else:
                            st.metric("Exclusions", 0)
                    with col3:
                        if 'Error' in status_counts:
                            st.metric("Errors", status_counts['Error'])
                        else:
                            st.metric("Errors", 0)
                    
                    # Top exclusion reasons
                    if status_filter != "Inclusion":
                        exclusion_df = filtered_df[filtered_df['Status'] == 'Exclusion']
                        if not exclusion_df.empty:
                            st.write("**Top Exclusion Reasons:**")
                            rationale_counts = exclusion_df['Rationale'].value_counts().head(10)
                            for reason, count in rationale_counts.items():
                                st.write(f"- {reason}: {count} cases")
                
                st.divider()
            
            # Log overall analysis completion
            total_analysis_duration = (datetime.now() - analysis_start_time).total_seconds()
            total_analysis_details = {
                'total_duration_seconds': total_analysis_duration,
                'psis_analyzed': len(selected_psis),
                'total_cases_processed': len(df_input) * len(selected_psis)
            }
            log_performance('full_analysis_completed', total_analysis_duration, total_analysis_details)
            log_user_activity('analysis_completed', total_analysis_details, 'success')
        
        else:
            st.warning("⚠️ Please select at least one PSI to analyze.")
            log_user_activity('analysis_attempted', {'error': 'no_psi_selected'}, 'warning')

    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        
        # Log the error with full context
        error_context = {
            'input_file': input_file.name if input_file else None,
            'appendix_file': appendix_file.name if appendix_file else None,
            'selected_psis': selected_psis,
            'debug_mode': debug_mode
        }
        log_error(e, error_context)
        log_user_activity('analysis_failed', error_context, 'error')
        
        if debug_mode:
            st.exception(e)
            
            # Show recent error logs
            with st.expander("🔍 Recent Error Logs"):
                try:
                    with open('logs/errors.log', 'r') as f:
                        lines = f.readlines()
                        recent_errors = lines[-5:]  # Last 5 errors
                        st.text_area("Recent Errors", "\n".join(recent_errors), height=200)
                except FileNotFoundError:
                    st.info("No error log file found")

else:
    st.info("📤 Please upload both the PSI Input Excel file and PSI Appendix Excel file to begin analysis.")
    log_user_activity('waiting_for_files')
    
    # Show sample data format
    with st.expander("📋 Expected Data Format"):
        st.markdown("""
        **Input Excel File should contain columns like:**
        - EncounterID or Encounter_ID
        - Age
        - MS-DRG
        - PrincipalDX
        - ATYPE (Admission Type: 1=Emergency, 2=Urgent, 3=Elective, 4=Newborn, 5=Not Available)
        - MDC (Major Diagnostic Category)
        - DRG (Diagnosis Related Group)
        - DX1, DX2, ..., DX30 (Diagnosis codes)
        - POA1, POA2, ..., POA30 (Present on Admission indicators: Y=Yes, N=No, U=Unknown, W=Clinically undetermined)
        - Proc1, Proc2, ..., Proc20 (Procedure codes)
        - Proc1_Date, Proc2_Date, ... (Procedure dates)
        - admission_date, discharge_date
        - length_of_stay
        
        **Appendix Excel File should contain:**
        - Code sets for each PSI (SEPTI2D, INFECID, ORPROC, etc.)
        - One column per code set with the corresponding ICD codes
        - Column names should match the expected code set names
        
        **Key Data Quality Requirements:**
        - All diagnosis codes should be in ICD-10-CM format
        - All procedure codes should be in ICD-10-PCS format
        - POA indicators are required for accurate PSI calculation
        - Procedure dates are required for timing-sensitive PSIs (13, 14, 15)
        - ATYPE field is required for PSI 13 (elective surgery indicator)
        """)

    # Show PSI Information
    with st.expander("ℹ️ PSI Information & Definitions"):
        st.markdown("""
        **Patient Safety Indicators (PSIs) Supported:**
        
        **PSI 05** - Foreign Object Retained After Surgery
        - Detects surgical items left inside patients
        
        **PSI 06** - Iatrogenic Pneumothorax Rate  
        - Identifies procedure-caused collapsed lung
        
        **PSI 07** - Central Venous Catheter-Related Blood Stream Infection Rate
        - Detects central line-associated bloodstream infections
        
        **PSI 08** - In-Hospital Fall with Hip Fracture Rate
        - Identifies hip fractures from hospital falls
        
        **PSI 09** - Perioperative Hemorrhage or Hematoma Rate
        - Detects surgical bleeding complications
        
        **PSI 10** - Postoperative Acute Kidney Injury Requiring Dialysis Rate
        - Identifies severe kidney injury after surgery
        
        **PSI 11** - Postoperative Respiratory Failure Rate
        - Detects respiratory failure requiring ventilation
        
        **PSI 12** - Perioperative Pulmonary Embolism or Deep Vein Thrombosis Rate
        - Identifies blood clots during hospitalization
        
        **PSI 13** - Postoperative Sepsis Rate
        - Detects serious infections after elective surgery
        
        **PSI 14** - Postoperative Wound Dehiscence Rate
        - Identifies surgical wounds that reopen
        
        **PSI 15** - Abdominopelvic Accidental Puncture or Laceration Rate
        - Detects accidental organ injuries during procedures
        
        **Features:**
        - ✅ AHRQ-compliant PSI logic
        - ✅ Comprehensive exclusion criteria
        - ✅ POA (Present on Admission) validation
        - ✅ Timing-based exclusions
        - ✅ Detailed rationale tracking
        - ✅ Multi-format export options
        - ✅ Debug mode for troubleshooting
        - ✅ **User activity logging**
        - ✅ **Error tracking and monitoring**
        - ✅ **Performance metrics**
        """)

# Log monitoring section for administrators
if debug_mode:
    with st.expander("🔧 Administrator - Log Monitoring"):
        st.markdown("**Log File Management:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("View User Activity Log"):
                try:
                    with open('logs/user_activity.log', 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-50:] if len(lines) > 50 else lines
                        st.text_area("User Activity (Last 50 entries)", "\n".join(recent_lines), height=300)
                except FileNotFoundError:
                    st.info("No user activity log found")
        
        with col2:
            if st.button("View Error Log"):
                try:
                    with open('logs/errors.log', 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-20:] if len(lines) > 20 else lines
                        st.text_area("Errors (Last 20 entries)", "\n".join(recent_lines), height=300)
                except FileNotFoundError:
                    st.info("No error log found")
        
        with col3:
            if st.button("View Performance Log"):
                try:
                    with open('logs/performance.log', 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-20:] if len(lines) > 20 else lines
                        st.text_area("Performance (Last 20 entries)", "\n".join(recent_lines), height=300)
                except FileNotFoundError:
                    st.info("No performance log found")
        
        # Log file statistics
        st.markdown("**Log Statistics:**")
        try:
            import os
            log_stats = {}
            log_files = ['logs/user_activity.log', 'logs/errors.log', 'logs/performance.log']
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    size = os.path.getsize(log_file)
                    with open(log_file, 'r') as f:
                        lines = len(f.readlines())
                    log_stats[log_file] = {'size_mb': size/1024/1024, 'lines': lines}
                else:
                    log_stats[log_file] = {'size_mb': 0, 'lines': 0}
            
            for log_file, stats in log_stats.items():
                st.write(f"**{log_file}:** {stats['lines']} entries, {stats['size_mb']:.2f} MB")
                
        except Exception as e:
            st.error(f"Error reading log statistics: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Enhanced PSI 05-15 Analyzer with User Logging</strong> - Advanced Patient Safety Indicator Analysis</p>
    <p>Built with Streamlit • Supports AHRQ PSI v2023 Specifications • Now with comprehensive logging</p>
    <p><em>For technical support or questions, please refer to AHRQ PSI documentation</em></p>
</div>
""", unsafe_allow_html=True)

# Log session end when app closes (best effort)
import atexit
def log_session_end():
    try:
        session_info = get_user_session_info()
        session_duration = (datetime.now() - session_info['session_start']).total_seconds()
        log_user_activity('session_ended', {'duration_seconds': session_duration})
    except:
        pass  # Ignore errors during cleanup

atexit.register(log_session_end)
