import streamlit as st
import pandas as pd
import numpy as np
import csv
from helpers.functions import *
import seaborn

# Add a tracking token
# html('<script async defer data-website-id="<your_website_id>" src="https://analytics.gnps2.org/umami.js"></script>', width=0, height=0)

# Write the page label
st.set_page_config(
    page_title="reverse metabolomics",
)

st.title("Reverse Metabolomics")


REDU_USEFUL_COLUMNS = ['SampleType',
       'SampleTypeSub1',
       'YearOfAnalysis', 'UBERONBodyPartName', 'BiologicalSex', 'AgeInYears',
       'LifeStage', 'Country', 'HealthStatus', 'ChromatographyAndPhase',
       'IonizationSourceAndPolarity', 'MassSpectrometer',
       'SampleExtractionMethod', 'SampleCollectionMethod',
       'ComorbidityListDOIDIndex', 'DOIDCommonName', 'DOIDOntologyIndex',
       'ENVOEnvironmentBiome', 'DepthorAltitudeMeters',
       'HumanPopulationDensity', 'InternalStandardsUsed',
       'LatitudeandLongitude', 'SampleCollectionDateandTime',
       'ENVOEnvironmentMaterial', 'ENVOEnvironmentBiomeIndex',
       'ENVOEnvironmentMaterialIndex', 'SubjectIdentifierAsRecorded',
       'TermsofPosition', 'UBERONOntologyIndex', 'UniqueSubjectID',
       'DataSource']

with open('data/unique_taxa.csv', 'r') as f:
    unique_taxa = [line.strip() for line in f.readlines()]



st.write("Upload FASST files you want to analyze from a GNPS FASST search. Multiple files can be uploaded at once.")
st.file_uploader("Upload FASST files here", 
                 type=["csv", "tsv", ],
                 key="fasst_uploader",
                 accept_multiple_files=True)

st.write("Select desired NCBI taxa to filter the data by in the sidebar.")
selected_taxa = st.multiselect("Select NCBI Taxa", options=unique_taxa, default=None)
fasst_files = st.session_state.get("fasst_uploader", [])

st.button("Submit NCBI Taxa", key="submit_taxa")



if st.session_state.get("start_merge", True) and "finished_merge" not in st.session_state:
    if not(len(fasst_files) > 0 and len(selected_taxa) > 0):
        st.error("Please upload FASST files and select at least one NCBI Taxonomy to filter by.")
        st.stop()

    # Read in redu metadata and filter by taxa
    redu_metadata = pd.read_csv("data/all_sampleinformation_redu_preprocessed.csv", dtype="str")
    redu_metadata = redu_metadata[redu_metadata["NCBITaxonomy"].isin(selected_taxa)]

    # drop columns with all NaN values
    redu_metadata = redu_metadata.replace({"missing value": pd.NA})
    redu_metadata = redu_metadata.dropna(axis=1, how='all')
    redu_metadata_columns = redu_metadata.columns.tolist()
    keep_columns = [col for col in redu_metadata_columns if col in REDU_USEFUL_COLUMNS]
    redu_metadata = redu_metadata[["USI"] + keep_columns]
    
    st.session_state["redu_metadata"] = redu_metadata
    st.session_state["fasst_files"] = fasst_files
    st.session_state["keep_columns"] = keep_columns
    st.session_state["show_column_selection"] = True
    st.session_state["finished_merge"] = True

if st.session_state.get("show_column_selection", True) and "show_column_selection" in st.session_state:
    column_chosen = st.selectbox("Select a column to visualize", options=st.session_state.get("keep_columns", []), key="column_selection")
    column_ready = st.button("Submit Column", key="column_ready")
    if column_ready:
        st.session_state["column_chosen"] = column_chosen
        st.session_state["show_variable_selection"] = True
        st.session_state["show_column_selection"] = False

if st.session_state.get("show_variable_selection", True) and "show_variable_selection" in st.session_state:
    print("show_variable_selection is True")
    redu_metadata = st.session_state.get("redu_metadata", pd.DataFrame())
    column_chosen = st.session_state.get("column_chosen")
    column_variables = redu_metadata[column_chosen].unique().tolist()
    column_variables = [var for var in column_variables if pd.notna(var) and var != "missing value"]
    selected_variables = st.multiselect("Select which variables you want to include", 
                                    options=column_variables, 
                                    default=column_variables, key="selected_variables")
    variables_ready = st.button("Submit Variables", key="variables_ready")
    if variables_ready:
        redu_metadata = redu_metadata[redu_metadata[column_chosen].isin(selected_variables)]
        st.session_state["redu_metadata"] = redu_metadata
        st.session_state["show_variable_selection"] = False
        st.session_state["show_data_table"] = True
    

if st.session_state.get("show_data_table", True) and "show_data_table" in st.session_state:
    redu_metadata = st.session_state.get("redu_metadata", pd.DataFrame())
    column_chosen = st.session_state.get("column_chosen", None)
    selected_variables = st.session_state.get("selected_variables", [])
    fasst_files = st.session_state.get("fasst_files", [])

    
    redu_metadata = redu_metadata[["USI"] + [column_chosen]]
    merged_fasst = pd.DataFrame()
    for file in fasst_files:
        if file is not None:
            filename = file.name.replace(".csv", "").replace(".tsv", "")
            if file.name.endswith(".csv"):
                df = pd.read_csv(file, dtype="str")
            else:
                df = pd.read_csv(file, sep="\t", dtype="str")
            df["Compound"] = filename
            merged_fasst = pd.concat([merged_fasst, df], ignore_index=True, axis =0)
    merged_fasst["Delta Mass"] = merged_fasst["Delta Mass"].astype(float, errors='ignore')
    merged_fasst = merged_fasst[merged_fasst["Delta Mass"].notna()]
    merged_fasst = merged_fasst[merged_fasst["Delta Mass"].abs() <= 0.05]    
    merged_fasst["USI"] = merged_fasst["USI"].apply(lambda x: process_USI(x))
    all_merged_data = pd.merge(merged_fasst, redu_metadata, on="USI", how="left")
    all_merged_data.dropna(subset=[column_chosen], inplace=True)
    st.write(f"Filtered data to {len(all_merged_data)} samples based on selected variables.")
    pivot_table = all_merged_data.groupby(column_chosen)["Compound"].value_counts(dropna=False).unstack(fill_value=0)
    # log transform the values
    pivot_table = pivot_table.applymap(lambda x: np.log2(x + 1))
    heatmap = seaborn.clustermap(pivot_table,
                             cmap="viridis",
                             figsize=(4, 10),
                             col_cluster=False)
    st.pyplot(heatmap)

