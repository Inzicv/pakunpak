import streamlit as st
import io

st.set_page_config(page_title="Générateur PAK/UNPAK Migration", layout="wide")

st.title("🧙‍♂️ Générateur de Scripts PAK & UNPAK")
st.subheader("Migration identique : \\ISIS ➔ \\LEIA")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 1. Sélection du Volume")
    vol_num = st.selectbox(
        "Sélectionner le numéro du volume",
        ["02", "03", "04", "05"],
        index=3
    )
    volume_full = f"$DEVT{vol_num}"
    
    # Utilisation de 2 antislashs en code pour en afficher UN seul à l'écran
    st.markdown(f"**Volume source :** `\\ISIS.{volume_full}`")
    st.markdown(f"**Volume destination :** `\\LEIA.{volume_full}`")

    subv_input = st.text_area(
        "Sous-volumes à migrer (un par ligne)",
        value="AVAKOBJ\nGAMKOBJ\nGESKOBJ\nSINKOBJ\nSCPKOBJ\nLGIKOBJ",
        help="Entrez les sous-volumes à copier"
    )

with col2:
    st.markdown("### 2. Règle de nommage automatique")
    pak_storage_subv = f"PAKMIG{vol_num}"
    st.info(f"📁 Sous-volume de stockage des PAK : `$DSMSCM.{pak_storage_subv}`")
    
    exclusions_input = st.text_input(
        "Exclusions (ex: ZZSA*) - Laissez vide si aucune",
        value="",
        help="Exemple: ZZSA* (s'appliquera sous la forme $VOL.$SUBV.ZZSA*)"
    )
    
    st.markdown("### 3. Paramètres PAK")
    pak_ext = st.number_input("Extent size (-ext)", value=50000)
    pak_split = st.number_input("Split size (-split)", value=1000000000)
    purge_opt = st.checkbox("Purger le fichier PAK existant (-purge)", value=True)

# Parsing des données
subvolumes = [s.strip().upper() for s in subv_input.split("\n") if s.strip()]

# Nettoyage des exclusions
exclusions = []
if exclusions_input.strip():
    exclusions = [e.strip().upper() for e in exclusions_input.split(",") if e.strip()]

if subvolumes:
    pak_lines = []
    unpak_lines = []
    purge_str = " -purge" if purge_opt else ""
    
    for subv in subvolumes:
        # Règle de nommage du fichier PAK : PK + 5 premières lettres
        short_subv = subv[:5] if len(subv) >= 5 else subv
        pak_filename = f"PK{short_subv}"
        
        if len(pak_filename) > 8:
            pak_filename = pak_filename[:8]
            
        full_pak_path = f"$DSMSCM.{pak_storage_subv}.{pak_filename}"
        
        # 1. Commande PAK
        pak_cmd = f"pak -ext {pak_ext} -split {pak_split}{purge_str} {full_pak_path} &\n"
        inc_path = f"({volume_full}.{subv}.*)"
        
        exc_parts = [f"not({volume_full}.{exc}.*)" for exc in exclusions]
        opts_path = ",listall,shareopen,audited"
        
        if exc_parts:
            pak_cmd += f"{inc_path}, {', '.join(exc_parts)}{opts_path}"
        else:
            pak_cmd += f"{inc_path}{opts_path}"
            
        pak_lines.append(pak_cmd)
        
        # 2. Commande UNPAK
        unpak_cmd = f"UNPAK {full_pak_path},\n*.*.*,MAP NAMES(*.*.* TO {volume_full}.{subv}.*)&\n,open,listall,audited"
        unpak_lines.append(unpak_cmd)

    # Assemblage
    obey_pak_content = "\n\n".join(pak_lines)
    obey_unpak_content = "\n\n".join(unpak_lines)

    st.markdown("---")
    st.markdown("### 🚀 Résultat des Scripts OBEY")

    tab1, tab2 = st.tabs(["Fichier OBEY - PAK (sur ISIS)", "Fichier OBEY - UNPAK (sur LEIA)"])
    
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
