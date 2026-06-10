import streamlit as st
import io

# Config globale
st.set_page_config(page_title="Outils de Migration Tandem", layout="wide")

# ==========================================
# PAGE 1 : GÉNÉRATEUR PAK & UNPAK (Ton code)
# ==========================================
def page_generateur():
    st.title("📦 Générateur d'obey PAK & UNPAK")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 1. Sélection du Volume")
        vol_num = st.selectbox(
            "Sélectionner le numéro du volume source/cible",
            ["02", "03", "04", "05"],
            index=3,
            key="gen_vol_num"
        )
        volume_full = f"$DEVT{vol_num}"

        machine_dest = st.selectbox(
            "Sélectionner la machine de destination (UNPAK)",
            ["\\LEIA", "\\PADME", "\\ISIS", "\\ATLAS", "Aucune (Pas de nœud)"],
            index=0,
            key="gen_machine_dest"
        )
        
        node_dest = "" if machine_dest == "Aucune (Pas de nœud)" else machine_dest

        st.markdown("### 2. Ciblage des fichiers")
        subv_input = st.text_area(
            "Sous-volumes à migrer (un par ligne)",
            value="AVAKTEST\nGAMRTEST\nGESVTEST\nSINUTEST\nSCPVABC\nLGIRABC",
            help="Entrez les sous-volumes à copier",
            key="gen_subv_input"
        )
        
        file_pattern = st.text_input(
            "Pattern des fichiers à inclure",
            value="*",
            help="Laissez '*' pour tout prendre, ou spécifiez (ex: I*, *OBJ, etc.)",
            key="gen_file_pattern"
        ).strip().upper()

        exclusions_input = st.text_input(
            "Exclusions de sous-volumes (ex: AVADABC) - Laissez vide si aucune",
            value="",
            help="Entrez les noms des sous-volumes à exclure du PAK",
            key="gen_exclusions"
        )

    with col2:
        st.markdown("### 3. Emplacement de stockage des PAK")
        
        pak_storage_vol = st.text_input(
            "Volume de stockage des PAK",
            value="$DSMSCM",
            key="gen_pak_vol"
        ).strip().upper()
        
        pak_storage_subv = st.text_input(
            "Sous-volume de stockage des PAK",
            value=f"PAKMIG{vol_num}",
            help="Par défaut basé sur ta règle de nommage, mais modifiable librement",
            key="gen_pak_subv"
        ).strip().upper()
        
        st.markdown("### 4. Paramètres PAK")
        pak_ext = st.number_input("Extent size (-ext)", value=50000, key="gen_ext")
        pak_split = st.number_input("Split size (-split)", value=1000000000, key="gen_split")
        purge_opt = st.checkbox("Purger le fichier PAK existant (-purge)", value=True, key="gen_purge")

    subvolumes = [s.strip().upper() for s in subv_input.split("\n") if s.strip()]

    exclusions = []
    if exclusions_input.strip():
        exclusions = [e.strip().upper() for e in exclusions_input.split(",") if e.strip()]

    if not file_pattern:
        file_pattern = "*"

    if not pak_storage_vol:
        pak_storage_vol = "$DSMSCM"
    if not pak_storage_subv:
        pak_storage_subv = f"PAKMIG{vol_num}"

    if subvolumes:
        pak_lines = []
        unpak_lines = []
        purge_str = " -purge" if purge_opt else ""
        
        for subv in subvolumes:
            short_subv = subv[:5] if len(subv) >= 5 else subv
            pak_filename = f"PK{short_subv}"
            
            if len(pak_filename) > 8:
                pak_filename = pak_filename[:8]
                
            full_pak_path = f"{pak_storage_vol}.{pak_storage_subv}.{pak_filename}"
            
            pak_cmd = f"pak -ext {pak_ext} -split {pak_split}{purge_str} {full_pak_path} &\n"
            inc_path = f"({volume_full}.{subv}.{file_pattern})"
            
            exc_parts = [f"not({volume_full}.{exc}.*)" for exc in exclusions]
            opts_path = ",listall,shareopen,audited"
            
            if exc_parts:
                pak_cmd += f"{inc_path}, {', '.join(exc_parts)}{opts_path}"
            else:
                pak_cmd += f"{inc_path}{opts_path}"
                
            pak_lines.append(pak_cmd)
            
            prefix_dest = f"{node_dest}." if node_dest else ""
            unpak_cmd = f"UNPAK {full_pak_path},\n*.*.*,MAP NAMES(*.*.{file_pattern} TO {prefix_dest}{volume_full}.{subv}.*)&\n,open,listall,audited"
            unpak_lines.append(unpak_cmd)

        obey_pak_content = "\n\n".join(pak_lines)
        obey_unpak_content = "\n\n".join(unpak_lines)

        st.markdown("---")
        st.markdown("### 🚀 Résultat des Scripts OBEY")

        tab1, tab2 = st.tabs(["Fichier OBEY - PAK (sur ISIS)", "Fichier OBEY - UNPAK (sur Cible)"])
        
        with tab1:
            st.code(obey_pak_content, language="text")
            st.download_button(
                label="📥 Télécharger OBEY_PAK.txt",
                data=obey_pak_content,
                file_name=f"OBEY_PAK_{volume_full.replace('$', '')}.txt",
                mime="text/plain"
            )
            
        with tab2:
            st.code(obey_unpak_content, language="text")
            st.download_button(
                label="📥 Télécharger OBEY_UNPAK.txt",
                data=obey_unpak_content,
                file_name=f"OBEY_UNPAK_{volume_full.replace('$', '')}.txt",
                mime="text/plain"
            )
    else:
        st.info("Ajoute des sous-volumes pour générer les commandes.")


# ==========================================
# PAGE 2 : VÉRIFICATEUR POST-COPIE (New!)
# ==========================================
def page_verificateur():
    st.title("🔍 Vérificateur Post-Copie (FILEINFO)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 1. Configuration du Check")
        vol_num = st.selectbox(
            "Volume à vérifier (Cible)",
            ["02", "03", "04", "05"],
            index=3,
            key="check_vol_num"
        )
        volume_full = f"$DEVT{vol_num}"
        
        subv_input = st.text_area(
            "Sous-volumes attendus (un par ligne)",
            value="AVAKTEST\nGAMRTEST\nGESVTEST\nSINUTEST\nSCPVABC\nLGIRABC",
            key="check_subv_input"
        )
        
        file_pattern = st.text_input(
            "Pattern des fichiers",
            value="*",
            key="check_file_pattern"
        ).strip().upper()
        
        # Génération du script de vérification
        subvolumes = [s.strip().upper() for s in subv_input.split("\n") if s.strip()]
        
        if subvolumes:
            # On génère des commandes short pour avoir un retour condensé et facile à parser dans la log
            fi_lines = [f"fileinfo {volume_full}.{subv}.{file_pattern}, short" for subv in subvolumes]
            obey_check_content = "\n".join(fi_lines)
            
            st.markdown("### 📋 Script OBEY de Vérification à exécuter")
            st.code(obey_check_content, language="text")
            st.download_button(
                label="📥 Télécharger OBEY_CHECK.txt",
                data=obey_check_content,
                file_name=f"OBEY_CHECK_{volume_full.replace('$', '')}.txt",
                mime="text/plain"
            )
            
    with col2:
        st.markdown("### 2. Analyse de la log Outside View")
        log_data = st.text_area(
            "Collez la log obtenue ici (ou glissez le fichier texte en dessous)",
            height=250,
            placeholder="Collez le retour TACL des commandes fileinfo..."
        )
        
        uploaded_log = st.file_uploader("Ou chargez un fichier de log", type=["txt", "log"])
        
        if uploaded_log is not None:
            log_data = io.StringIO(uploaded_log.getvalue().decode("utf-8")).read()
            
        if st.button("🔎 Analyser la log", type="primary"):
            if not log_data.strip():
                st.warning("Veuillez fournir une log à analyser.")
            elif not subvolumes:
                st.warning("Aucun sous-volume spécifié pour la comparaison.")
            else:
                st.markdown("### 📊 Rapport de vérification")
                
                log_upper = log_data.upper()
                manqu
