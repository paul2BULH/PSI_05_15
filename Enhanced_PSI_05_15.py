                # Check for retained surgical items
                target_codes = code_sets.get("FOREIID_CODES", [])
                matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                          if pos == "SECONDARY" and dx in target_codes and poa != "Y"]
                
                if matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Retained surgical item found: {matches[0][0]} (POA: {matches[0][1]})")
                    detailed_info["matched_codes"] = matches
                else:
                    rationale.append("No qualifying retained surgical item codes found")

            elif psi_name == "PSI_06":
                # Population inclusion
                surgical_medical = (ms_drg in code_sets.get("SURGI2R_CODES", []) or 
                                  ms_drg in code_sets.get("MEDIC2R_CODES", []))
                if not surgical_medical:
                    rationale.append("Not surgical or medical DRG")
                    return psi_status, rationale, detailed_info
                
                # Exclusions
                if principal_dx in code_sets.get("IATPTXD_CODES", []):
                    rationale.append("Principal diagnosis of non-traumatic pneumothorax")
                    return psi_status, rationale, detailed_info
                
                # Check for chest trauma
                trauma_codes = code_sets.get("CTRAUMD_CODES", [])
                if any(dx in trauma_codes for dx, poa, pos, seq in dx_list):
                    rationale.append("Chest trauma diagnosis present")
                    return psi_status, rationale, detailed_info
                
                # Check for iatrogenic pneumothorax
                target_codes = code_sets.get("IATROID_CODES", [])
                matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                          if pos == "SECONDARY" and dx in target_codes and poa != "Y"]
                
                if matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Iatrogenic pneumothorax found: {matches[0][0]} (POA: {matches[0][1]})")
                    detailed_info["matched_codes"] = matches
                else:
                    rationale.append("No qualifying iatrogenic pneumothorax codes found")

            elif psi_name == "PSI_07":
                # Population inclusion
                surgical_medical = (ms_drg in code_sets.get("SURGI2R_CODES", []) or 
                                  ms_drg in code_sets.get("MEDIC2R_CODES", []) or
                                  principal_dx in code_sets.get("MDC14PRINDX_CODES", []))
                if not surgical_medical:
                    rationale.append("Not surgical, medical, or obstetric case")
                    return psi_status, rationale, detailed_info
                
                # Length of stay check
                if pd.notna(length_of_stay) and length_of_stay < 2:
                    rationale.append(f"Length of stay < 2 days: {length_of_stay}")
                    return psi_status, rationale, detailed_info
                
                # Cancer exclusion
                cancer_codes = code_sets.get("CANCEID_CODES", [])
                if any(dx in cancer_codes for dx, poa, pos, seq in dx_list):
                    rationale.append("Cancer diagnosis present")
                    return psi_status, rationale, detailed_info
                
                # Check for central line infections
                target_codes = code_sets.get("IDTMC3D_CODES", [])
                matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                          if pos == "SECONDARY" and dx in target_codes and poa != "Y"]
                
                if matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Central line infection found: {matches[0][0]} (POA: {matches[0][1]})")
                    detailed_info["matched_codes"] = matches
                else:
                    rationale.append("No qualifying central line infection codes found")

            elif psi_name == "PSI_08":
                # Population inclusion (adults ≥18 in surgical/medical)
                surgical_medical = (ms_drg in code_sets.get("SURGI2R_CODES", []) or 
                                  ms_drg in code_sets.get("MEDIC2R_CODES", []))
                if not surgical_medical:
                    rationale.append("Not surgical or medical DRG")
                    return psi_status, rationale, detailed_info
                
                # Prosthetic fracture exclusion
                prosthetic_codes = code_sets.get("PROSFXID_CODES", [])
                if any(dx in prosthetic_codes for dx, poa, pos, seq in dx_list):
                    rationale.append("Prosthetic fracture present")
                    return psi_status, rationale, detailed_info
                
                # Fracture hierarchy logic
                fxid_codes = code_sets.get("FXID_CODES", [])
                hipfx_codes = code_sets.get("HIPFXID_CODES", [])
                
                fracture_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                                  if pos == "SECONDARY" and dx in fxid_codes and poa != "Y"]
                
                if fracture_matches:
                    # Check for hip fractures first (priority)
                    hip_matches = [match for match in fracture_matches if match[0] in hipfx_codes]
                    if hip_matches:
                        psi_status = "Inclusion"
                        rationale.append(f"Hip fracture found: {hip_matches[0][0]} (takes priority)")
                        detailed_info["fracture_type"] = "hip"
                    else:
                        psi_status = "Inclusion"
                        rationale.append(f"Other fracture found: {fracture_matches[0][0]}")
                        detailed_info["fracture_type"] = "other"
                    detailed_info["matched_codes"] = fracture_matches
                else:
                    rationale.append("No qualifying fracture codes found")

            elif psi_name == "PSI_09":
                # Population inclusion (surgical only)
                if ms_drg not in code_sets.get("SURGI2R_CODES", []):
                    rationale.append("Not surgical DRG")
                    return psi_status, rationale, detailed_info
                
                # Must have OR procedure
                or_codes = code_sets.get("ORPROC_CODES", [])
                or_procs = [code for code, dt, seq in proc_list if code in or_codes]
                if not or_procs:
                    rationale.append("No operating room procedures found")
                    return psi_status, rationale, detailed_info
                
                # Coagulation disorder exclusion
                coag_codes = code_sets.get("COAGDID_CODES", [])
                if any(dx in coag_codes for dx, poa, pos, seq in dx_list):
                    rationale.append("Coagulation disorder present")
                    return psi_status, rationale, detailed_info
                
                # Dual requirement: diagnosis AND procedure
                dx_codes = code_sets.get("POHMRI2D_CODES", [])
                dx_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                             if pos == "SECONDARY" and dx in dx_codes and poa != "Y"]
                
                proc_codes = code_sets.get("HEMOTH2P_CODES", [])
                proc_matches = [code for code, dt, seq in proc_list if code in proc_codes]
                
                if dx_matches and proc_matches:
                    # Check timing if possible
                    timing_issue, timing_msg = check_timing_exclusions(
                        proc_list, or_codes, proc_codes, admit_date)
                    if timing_issue:
                        rationale.append(f"Timing exclusion: {timing_msg}")
                        return psi_status, rationale, detailed_info
                    
                    psi_status = "Inclusion"
                    rationale.append(f"Both hemorrhage diagnosis and treatment found")
                    detailed_info["dx_matches"] = dx_matches
                    detailed_info["proc_matches"] = proc_matches
                elif dx_matches:
                    rationale.append("Hemorrhage diagnosis found but no treatment procedure")
                elif proc_matches:
                    rationale.append("Treatment procedure found but no hemorrhage diagnosis")
                else:
                    rationale.append("Neither hemorrhage diagnosis nor treatment procedure found")

            elif psi_name == "PSI_10":
                # Population inclusion (surgical only)
                if ms_drg not in code_sets.get("SURGI2R_CODES", []):
                    rationale.append("Not surgical DRG")
                    return psi_status, rationale, detailed_info
                
                # Cardiac condition exclusions
                cardiac_codes = (code_sets.get("CARDIID_CODES", []) + 
                               code_sets.get("CARDRID_CODES", []) + 
                               code_sets.get("SHOCKID_CODES", []) +
                               code_sets.get("CRENLFD_CODES", []))
                
                cardiac_exclusions = [(dx, poa, pos) for dx, poa, pos, seq in dx_list 
                                    if dx in cardiac_codes and (pos == "PRINCIPAL" or poa == "Y")]
                if cardiac_exclusions:
                    rationale.append(f"Cardiac/kidney condition exclusion: {cardiac_exclusions[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Dual requirement: kidney failure AND dialysis
                dx_codes = code_sets.get("PHYSIDB_CODES", [])
                dx_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                             if pos == "SECONDARY" and dx in dx_codes and poa != "Y"]
                
                proc_codes = code_sets.get("DIALYIP_CODES", [])
                proc_matches = [code for code, dt, seq in proc_list if code in proc_codes]
                
                if dx_matches and proc_matches:
                    psi_status = "Inclusion"
                    rationale.append(f"Both kidney failure and dialysis found")
                    detailed_info["dx_matches"] = dx_matches
                    detailed_info["proc_matches"] = proc_matches
                else:
                    rationale.append("Missing kidney failure diagnosis or dialysis procedure")

            elif psi_name == "PSI_11":
                # Population inclusion (elective surgical only)
                if atype != 3:
                    rationale.append(f"Not elective admission: ATYPE = {atype}")
                    return psi_status, rationale, detailed_info
                
                if ms_drg not in code_sets.get("SURGI2R_CODES", []):
                    rationale.append("Not surgical DRG")
                    return psi_status, rationale, detailed_info
                
                # Neurological exclusions
                neuro_codes = code_sets.get("NEUROMD_CODES", []) + code_sets.get("MALHYPD_CODES", [])
                neuro_exclusions = [(dx, poa) for dx, poa, pos, seq in dx_list 
                                  if dx in neuro_codes and poa == "Y"]
                if neuro_exclusions:
                    rationale.append(f"Neurological condition exclusion: {neuro_exclusions[0][0]}")
                    return psi_status, rationale, detailed_info
                
                # Multiple criteria check
                criteria_met = []
                
                # Criteria 1: Respiratory failure diagnosis
                resp_codes = code_sets.get("ACURF2D_CODES", [])
                resp_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                              if pos == "SECONDARY" and dx in resp_codes and poa != "Y"]
                if resp_matches:
                    criteria_met.append("respiratory_failure_diagnosis")
                
                # Criteria 2-4: Ventilation/intubation procedures
                vent_codes = (code_sets.get("PR9672P_CODES", []) + 
                            code_sets.get("PR9671P_CODES", []) + 
                            code_sets.get("PR9604P_CODES", []))
                vent_matches = [code for code, dt, seq in proc_list if code in vent_codes]
                if vent_matches:
                    criteria_met.append("ventilation_procedures")
                
                if criteria_met:
                    psi_status = "Inclusion"
                    rationale.append(f"Respiratory failure criteria met: {', '.join(criteria_met)}")
                    detailed_info["criteria_met"] = criteria_met
                else:
                    rationale.append("No respiratory failure criteria met")

            elif psi_name == "PSI_12":
                # Population inclusion (surgical only)
                if ms_drg not in code_sets.get("SURGI2R_CODES", []):
                    rationale.append("Not surgical DRG")
                    return psi_status, rationale, detailed_info
                
                # Must have OR procedure
                or_codes = code_sets.get("ORPROC_CODES", [])
                or_procs = [code for code, dt, seq in proc_list if code in or_codes]
                if not or_procs:
                    rationale.append("No operating room procedures found")
                    return psi_status, rationale, detailed_info
                
                # HIT exclusion
                hit_codes = code_sets.get("HITD_CODES", [])
                if any(dx in hit_codes for dx, poa, pos, seq in dx_list if pos == "SECONDARY"):
                    rationale.append("Heparin-induced thrombocytopenia present")
                    return psi_status, rationale, detailed_info
                
                # DVT/PE check
                dvt_codes = code_sets.get("DEEPVIB_CODES", [])
                pe_codes = code_sets.get("PULMOID_CODES", [])
                
                dvt_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                              if pos == "SECONDARY" and dx in dvt_codes and poa != "Y"]
                pe_matches = [(dx, poa) for dx, poa, pos, seq in dx_list 
                             if pos == "SECONDARY" and dx in pe_codes and poa != "Y"]
                
                if dvt_matches or pe_matches:
                    psi_status = "Inclusion"
                    event_type = []
                    if dvt_matches:
                        event_type.append("DVT")
                    if pe_matches:
                        event_type.append("PE")
                    rationale.append(f"VTE event found: {', '.join(event_type)}")
                    detailed_info["dvt_matches"] = dvt_matches
                    detailed_info["pe_matches"] = pe_matches
                else:
                    rationale.append("No qualifying DVT or PE codes found")
            
            return psi_status, rationale, detailed_info

        # Process all data
        results = []
        progress_bar = st.progress(0)
        total_rows = len(df_input)
        
        for idx, row in df_input.iterrows():
            progress_bar.progress((idx + 1) / total_rows)
            
            enc_id = row.get("EncounterID") or row.get("Encounter_ID") or f"Row_{idx+1}"
            
            for psi_name in selected_psis:
                psi_status, rationale, detailed_info = evaluate_psi_comprehensive(
                    row, psi_name, code_sets, debug_mode)
                
                result_row = {
                    "EncounterID": enc_id,
                    "PSI": psi_name,
                    "Status": psi_status,
                    "Rationale": " | ".join(rationale),
                    "Age": row.get("Age", ""),
                    "MS_DRG": row.get("MS-DRG", ""),
                    "Principal_DX": row.get("PrincipalDX", ""),
                    "ATYPE": row.get("ATYPE", ""),
                    "LOS": row.get("length_of_stay", "")
                }
                
                if debug_mode and detailed_info:
                    result_row["Debug_Info"] = json.dumps(detailed_info, default=str)
                
                results.append(result_row)

        progress_bar.empty()
        
        # Display results
        st.success(f"✅ Enhanced PSI {', '.join(selected_psis)} analysis complete!")
        
        df_result = pd.DataFrame(results)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_encounters = df_result['EncounterID'].nunique()
            st.metric("Total Encounters", total_encounters)
        
        with col2:
            total_inclusions = len(df_result[df_result['Status'] == 'Inclusion'])
            st.metric("PSI Triggers", total_inclusions)
        
        with col3:
            inclusion_rate = (total_inclusions / len(df_result) * 100) if len(df_result) > 0 else 0
            st.metric("Trigger Rate", f"{inclusion_rate:.1f}%")
        
        with col4:
            unique_psi_triggers = df_result[df_result['Status'] == 'Inclusion']['PSI'].nunique()
            st.metric("PSI Types Triggered", unique_psi_triggers)

        # PSI Summary
        st.subheader("📊 PSI Summary by Type")
        psi_summary = df_result.groupby(['PSI', 'Status']).size().unstack(fill_value=0)
        st.dataframe(psi_summary, use_container_width=True)
        
        # Advanced Analysis for PSI 13-15
        if any(psi in selected_psis for psi in ["PSI_13", "PSI_14", "PSI_15"]):
            st.subheader("🔬 Advanced Analysis for PSI 13-15")
            
            # PSI 13 Analysis
            if "PSI_13" in selected_psis:
                psi13_results = df_result[df_result['PSI'] == 'PSI_13']
                if not psi13_results.empty:
                    st.write("**PSI 13 - Postoperative Sepsis Analysis:**")
                    
                    # Elective surgery breakdown
                    elective_breakdown = []
                    for _, row in df_input.iterrows():
                        atype = row.get("ATYPE")
                        ms_drg = str(row.get("MS-DRG", ""))
                        elective_breakdown.append({
                            "EncounterID": row.get("EncounterID", f"Row_{_}"),
                            "ATYPE": atype,
                            "Is_Elective": atype == 3,
                            "Is_Surgical": ms_drg in code_sets.get("SURGI2R_CODES", [])
                        })
                    
                    elective_df = pd.DataFrame(elective_breakdown)
                    elective_summary = elective_df.groupby(['Is_Elective', 'Is_Surgical']).size().unstack(fill_value=0)
                    st.write("Elective Surgical Population Breakdown:")
                    st.dataframe(elective_summary)
            
            # PSI 14 Analysis
            if "PSI_14" in selected_psis:
                psi14_results = df_result[df_result['PSI'] == 'PSI_14']
                if not psi14_results.empty:
                    st.write("**PSI 14 - Wound Dehiscence Stratum Analysis:**")
                    
                    # Extract stratum information from debug info
                    stratum_data = []
                    for _, row in psi14_results.iterrows():
                        if row.get('Debug_Info'):
                            try:
                                debug_info = json.loads(row['Debug_Info'])
                                stratum = debug_info.get('stratum', 'Unknown')
                                stratum_data.append({
                                    "EncounterID": row['EncounterID'],
                                    "Status": row['Status'],
                                    "Stratum": stratum
                                })
                            except:
                                pass
                    
                    if stratum_data:
                        stratum_df = pd.DataFrame(stratum_data)
                        stratum_summary = stratum_df.groupby(['Stratum', 'Status']).size().unstack(fill_value=0)
                        st.dataframe(stratum_summary)
            
            # PSI 15 Analysis
            if "PSI_15" in selected_psis:
                psi15_results = df_result[df_result['PSI'] == 'PSI_15']
                if not psi15_results.empty:
                    st.write("**PSI 15 - Organ-Specific Injury Analysis:**")
                    
                    # Extract organ-specific information
                    organ_data = []
                    for _, row in psi15_results.iterrows():
                        if row.get('Debug_Info'):
                            try:
                                debug_info = json.loads(row['Debug_Info'])
                                qualifying_organs = debug_info.get('qualifying_organs', [])
                                for organ in qualifying_organs:
                                    organ_data.append({
                                        "EncounterID": row['EncounterID'],
                                        "Organ_System": organ,
                                        "Status": row['Status']
                                    })
                            except:
                                pass
                    
                    if organ_data:
                        organ_df = pd.DataFrame(organ_data)
                        organ_summary = organ_df.groupby(['Organ_System', 'Status']).size().unstack(fill_value=0)
                        st.write("Injuries by Organ System:")
                        st.dataframe(organ_summary)

        # Filters
        st.subheader("🔍 Detailed Results")
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Inclusion", "Exclusion"])
        with col2:
            psi_filter = st.selectbox("Filter by PSI", ["All"] + sorted(df_result['PSI'].unique()))
        with col3:
            encounter_search = st.text_input("Search Encounter ID")
        
        # Apply filters
        filtered_df = df_result.copy()
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['Status'] == status_filter]
        if psi_filter != "All":
            filtered_df = filtered_df[filtered_df['PSI'] == psi_filter]
        if encounter_search:
            filtered_df = filtered_df[filtered_df['EncounterID'].str.contains(encounter_search, case=False, na=False)]
        
        # Display filtered results
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download Full Results", 
                df_result.to_csv(index=False), 
                "Enhanced_PSI_05-15_Results.csv",
                mime="text/csv"
            )
        with col2:
            if not filtered_df.empty:
                st.download_button(
                    "📥 Download Filtered Results", 
                    filtered_df.to_csv(index=False), 
                    "Filtered_PSI_Results.csv",
                    mime="text/csv"
                )

        # Code set validation
        if st.expander("🔧 Code Set Validation"):
            st.write("**Loaded Code Sets:**")
            
            # Organize by PSI
            psi_code_mapping = {
                "PSI_13": ["SEPTI2D_CODES", "INFECID_CODES"],
                "PSI_14": ["RECLOIP_CODES", "ABWALLCD_CODES", "ABDOMIPOPEN_CODES", "ABDOMIPOTHER_CODES"],
                "PSI_15": ["ABDOMI15P_CODES", "SPLEEN15D_CODES", "SPLEEN15P_CODES", "ADRENAL15D_CODES", 
                          "ADRENAL15P_CODES", "VESSEL15D_CODES", "VESSEL15P_CODES", "DIAPHR15D_CODES", 
                          "DIAPHR15P_CODES", "GI15D_CODES", "GI15P_CODES", "GU15D_CODES", "GU15P_CODES"]
            }
            
            for psi_name in ["PSI_13", "PSI_14", "PSI_15"]:
                if psi_name in selected_psis:
                    with st.expander(f"📋 {psi_name} Code Sets"):
                        for code_name in psi_code_mapping.get(psi_name, []):
                            if code_name in code_sets:
                                codes = code_sets[code_name]
                                st.write(f"**{code_name}**: {len(codes)} codes")
                                if st.checkbox(f"Show {code_name} codes", key=f"show_{code_name}"):
                                    st.code(", ".join(codes[:20]) + ("..." if len(codes) > 20 else ""))
            
            # Common codes
            with st.expander("📋 Common Code Sets"):
                common_codes = ["SURGI2R_CODES", "MEDIC2R_CODES", "MDC14PRINDX_CODES", "MDC15PRINDX_CODES", "ORPROC_CODES"]
                for code_name in common_codes:
                    if code_name in code_sets:
                        codes = code_sets[code_name]
                        st.write(f"**{code_name}**: {len(codes)} codes")
                        if st.checkbox(f"Show {code_name} codes", key=f"show_common_{code_name}"):
                            st.code(", ".join(codes[:20]) + ("..." if len(codes) > 20 else ""))

    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        if debug_mode:
            st.exception(e)

else:
    st.info("📋 Please upload both input and appendix Excel files to begin analysis.")
    
    # Enhanced Instructions for PSI 13-15
    with st.expander("📖 Instructions for Use (Updated for PSI 13-15)"):
        st.markdown("""
        ### Required Excel File Format
        
        **Input File (PSI Data):**
        - EncounterID or Encounter_ID: Unique identifier
        - Age: Patient age (must be ≥18)
        - MS-DRG: MS-DRG code
        - PrincipalDX: Principal diagnosis (ICD-10-CM without decimals)
        - DX1-DX30: Additional diagnoses
        - POA1-POA30: Present on Admission indicators (Y/N/U/W)
        - Proc1-Proc20: Procedure codes (ICD-10-PCS) - **Extended for PSI 14/15**
        - Proc1_Date-Proc20_Date: Procedure dates - **Required for PSI 14/15**
        - ATYPE: Admission type (3 = elective, **required for PSI 13**)
        - admission_date, discharge_date: For timing calculations
        - length_of_stay: Length of stay in days (**required for PSI 14**)
        
        **Appendix File (Code Sets) - Enhanced for PSI 13-15:**
        
        **PSI 13 Code Sets:**
        - SEPTI2D: Sepsis diagnosis codes
        - INFECID: General infection diagnosis codes
        
        **PSI 14 Code Sets:**
        - RECLOIP: Abdominal wall reclosure procedure codes
        - ABWALLCD: Wound disruption diagnosis codes
        - ABDOMIPOPEN: Open abdominopelvic surgery codes
        - ABDOMIPOTHER: Non-open abdominopelvic surgery codes
        
        **PSI 15 Code Sets (Organ-Specific):**
        - ABDOMI15P: Index abdominopelvic procedure codes
        - SPLEEN15D/SPLEEN15P: Spleen injury/procedure codes
        - ADRENAL15D/ADRENAL15P: Adrenal injury/procedure codes
        - VESSEL15D/VESSEL15P: Vessel injury/procedure codes
        - DIAPHR15D/DIAPHR15P: Diaphragm injury/procedure codes
        - GI15D/GI15P: GI tract injury/procedure codes
        - GU15D/GU15P: GU system injury/procedure codes
        
        ### New Features for PSI 13-15
        - ✅ **PSI 13**: Elective surgery validation with timing exclusions
        - ✅ **PSI 14**: Dual numerator requirements with stratification
        - ✅ **PSI 15**: Organ-specific matching with time window analysis
        - ✅ Advanced timing validation for complex procedures
        - ✅ Enhanced POA logic for multiple condition types
        - ✅ Detailed debugging for complex logic flows
        """)
    
    with st.expander("🎯 PSI 13-15 Specific Logic"):
        st.markdown("""
        ### PSI 13 - Postoperative Sepsis Rate
        - **Population**: Elective surgical patients ≥18 (ATYPE=3)
        - **Requirements**: Must have OR procedure
        - **Exclusions**: Principal/POA sepsis, principal/POA infections, late surgery (≥10 days)
        - **Numerator**: Secondary sepsis diagnosis (not POA)
        - **Focus**: Preventable postoperative infections
        
        ### PSI 14 - Postoperative Wound Dehiscence Rate  
        - **Population**: Patients ≥18 with abdominopelvic surgery
        - **Dual Requirements**: BOTH reclosure procedure AND wound disruption diagnosis
        - **Stratification**: Open approach vs. non-open approach (mutually exclusive)
        - **Exclusions**: Principal/POA wound disruption, LOS < 2 days, timing issues
        - **Timing Logic**: Reclosure must occur AFTER initial surgery
        
        ### PSI 15 - Abdominopelvic Accidental Puncture/Laceration Rate
        - **Population**: Medical/surgical patients ≥18 with abdominopelvic procedures
        - **Triple Requirements**: Injury diagnosis AND related procedure AND timing (1-30 days)
        - **Organ Systems**: Spleen, Adrenal, Vessel, Diaphragm, GI, GU (6 systems)
        - **Matching Logic**:# enhanced_psi_web_debugger_extended.py

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