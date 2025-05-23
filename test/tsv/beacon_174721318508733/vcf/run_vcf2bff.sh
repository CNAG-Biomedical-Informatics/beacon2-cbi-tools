#!/usr/bin/env bash
#
#   Script that generates BFF format from VCF
#
#   Last Modified: Mar/17/2025
#
#   Version taken from $BEACON
#
#   Copyright (C) 2021-2022 Manuel Rueda - CRG
#   Copyright (C) 2023-2025 Manuel Rueda - CNAG (manuel.rueda@cnag.eu)
#
#   Credits: Dietmar Fernandez-Orth for creating bcftools/snpEff commands
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <https://www.gnu.org/licenses/>.
#
#   If this program helps you in your research, please cite.

set -euo pipefail
export LC_ALL=C

export TMPDIR=/media/mrueda/2TBS/tmp
ZIP='/usr/bin/pigz -p 11'
SNPEFF='/usr/bin/java -Xmx8G -jar /media/mrueda/2TBS/NGSutils/snpEff_v5.0/snpEff.jar'
SNPSIFT='/usr/bin/java -Xmx8G -jar /media/mrueda/2TBS/NGSutils/snpEff_v5.0/SnpSift.jar'
BCFTOOLS=/media/mrueda/2TBS/NGSutils/bcftools-1.21-103_x86_64/bcftools
VCF2BFF=/media/mrueda/2TBS/CNAG/Project_Beacon/beacon2-cbi-tools/lib/internal/complete/vcf2bff.pl
GENOME='hg19'
REF=/media/mrueda/2TBS/Databases/genomes/hs37d5.fa.gz
COSMIC=/media/mrueda/2TBS/Databases/snpeff/v5.0/hg19/CosmicCodingMuts.normal.hg19.vcf.gz
DBNSFP=/media/mrueda/2TBS/Databases/snpeff/v5.0/hg19/dbNSFP4.1a_hg19.txt.gz
DATASETID=default_beacon_1
PROJECTDIR=beacon_174721318508733
CLINVAR=/media/mrueda/2TBS/Databases/snpeff/v5.0/hg19/clinvar_20250312.vcf.gz

function usage {
    echo "Usage: $0 <input_vcf> [annotation:true|false]"
    exit 1
}

# Check if at least one argument (input VCF) is provided
if [ $# -lt 1 ]; then
    usage
fi

# Load input arguments
INPUT_VCF=$1
# Optional second argument determines whether to run full annotation steps (default is false)
ANNOTATION=${2:-false}
BASE=$(basename "$INPUT_VCF" .vcf.gz)

if [ "$ANNOTATION" == "true" ]; then
    echo "# Running bcftools normalization"
    $BCFTOOLS norm -cs -m -both "$INPUT_VCF" -f "$REF" -Oz -o "$BASE.norm.vcf.gz"
    
    echo "# Running SnpEff annotation"
    $SNPEFF -noStats -i vcf -o vcf "$GENOME" "$BASE.norm.vcf.gz" | $ZIP > "$BASE.norm.ann.vcf.gz"
    
    echo "# Running SnpSift dbNSFP annotation"
    $SNPSIFT dbnsfp -v -db "$DBNSFP" -f 'hg18_pos(1-based)','hg19_pos(1-based)','pos(1-based)',1000Gp3_AC,1000Gp3_AF,1000Gp3_AFR_AC,1000Gp3_AFR_AF,1000Gp3_AMR_AC,1000Gp3_AMR_AF,1000Gp3_EAS_AC,1000Gp3_EAS_AF,1000Gp3_EUR_AC,1000Gp3_EUR_AF,1000Gp3_SAS_AC,1000Gp3_SAS_AF,ALSPAC_AC,ALSPAC_AF,APPRIS,Aloft_Confidence,Aloft_Fraction_transcripts_affected,Aloft_pred,Aloft_prob_Dominant,Aloft_prob_Recessive,Aloft_prob_Tolerant,AltaiNeandertal,Ancestral_allele,BayesDel_addAF_pred,BayesDel_addAF_rankscore,BayesDel_addAF_score,BayesDel_noAF_pred,BayesDel_noAF_rankscore,BayesDel_noAF_score,CADD_phred,CADD_phred_hg19,CADD_raw,CADD_raw_hg19,CADD_raw_rankscore,CADD_raw_rankscore_hg19,ClinPred_pred,ClinPred_rankscore,ClinPred_score,DANN_rankscore,DANN_score,DEOGEN2_pred,DEOGEN2_rankscore,DEOGEN2_score,Denisova,ESP6500_AA_AC,ESP6500_AA_AF,ESP6500_EA_AC,ESP6500_EA_AF,Eigen-PC-phred_coding,Eigen-PC-raw_coding,Eigen-PC-raw_coding_rankscore,Eigen-phred_coding,Eigen-raw_coding,Eigen-raw_coding_rankscore,Ensembl_geneid,Ensembl_proteinid,Ensembl_transcriptid,ExAC_AC,ExAC_AF,ExAC_AFR_AC,ExAC_AFR_AF,ExAC_AMR_AC,ExAC_AMR_AF,ExAC_Adj_AC,ExAC_Adj_AF,ExAC_EAS_AC,ExAC_EAS_AF,ExAC_FIN_AC,ExAC_FIN_AF,ExAC_NFE_AC,ExAC_NFE_AF,ExAC_SAS_AC,ExAC_SAS_AF,ExAC_nonTCGA_AC,ExAC_nonTCGA_AF,ExAC_nonTCGA_AFR_AC,ExAC_nonTCGA_AFR_AF,ExAC_nonTCGA_AMR_AC,ExAC_nonTCGA_AMR_AF,ExAC_nonTCGA_Adj_AC,ExAC_nonTCGA_Adj_AF,ExAC_nonTCGA_EAS_AC,ExAC_nonTCGA_EAS_AF,ExAC_nonTCGA_FIN_AC,ExAC_nonTCGA_FIN_AF,ExAC_nonTCGA_NFE_AC,ExAC_nonTCGA_NFE_AF,ExAC_nonTCGA_SAS_AC,ExAC_nonTCGA_SAS_AF,ExAC_nonpsych_AC,ExAC_nonpsych_AF,ExAC_nonpsych_AFR_AC,ExAC_nonpsych_AFR_AF,ExAC_nonpsych_AMR_AC,ExAC_nonpsych_AMR_AF,ExAC_nonpsych_Adj_AC,ExAC_nonpsych_Adj_AF,ExAC_nonpsych_EAS_AC,ExAC_nonpsych_EAS_AF,ExAC_nonpsych_FIN_AC,ExAC_nonpsych_FIN_AF,ExAC_nonpsych_NFE_AC,ExAC_nonpsych_NFE_AF,ExAC_nonpsych_SAS_AC,ExAC_nonpsych_SAS_AF,FATHMM_converted_rankscore,FATHMM_pred,FATHMM_score,GENCODE_basic,GERP++_NR,GERP++_RS,GERP++_RS_rankscore,GM12878_confidence_value,GM12878_fitCons_rankscore,GM12878_fitCons_score,GTEx_V8_gene,GTEx_V8_tissue,GenoCanyon_rankscore,GenoCanyon_score,Geuvadis_eQTL_target_gene,H1-hESC_confidence_value,H1-hESC_fitCons_rankscore,H1-hESC_fitCons_score,HGVSc_ANNOVAR,HGVSc_VEP,HGVSc_snpEff,HGVSp_ANNOVAR,HGVSp_VEP,HGVSp_snpEff,HUVEC_confidence_value,HUVEC_fitCons_rankscore,HUVEC_fitCons_score,Interpro_domain,LINSIGHT,LINSIGHT_rankscore,LIST-S2_pred,LIST-S2_rankscore,LIST-S2_score,LRT_Omega,LRT_converted_rankscore,LRT_pred,LRT_score,M-CAP_pred,M-CAP_rankscore,M-CAP_score,MPC_rankscore,MPC_score,MVP_rankscore,MVP_score,MetaLR_pred,MetaLR_rankscore,MetaLR_score,MetaSVM_pred,MetaSVM_rankscore,MetaSVM_score,MutPred_AAchange,MutPred_Top5features,MutPred_protID,MutPred_rankscore,MutPred_score,MutationAssessor_pred,MutationAssessor_rankscore,MutationAssessor_score,MutationTaster_AAE,MutationTaster_converted_rankscore,MutationTaster_model,MutationTaster_pred,MutationTaster_score,PROVEAN_converted_rankscore,PROVEAN_pred,PROVEAN_score,Polyphen2_HDIV_pred,Polyphen2_HDIV_rankscore,Polyphen2_HDIV_score,Polyphen2_HVAR_pred,Polyphen2_HVAR_rankscore,Polyphen2_HVAR_score,PrimateAI_pred,PrimateAI_rankscore,PrimateAI_score,REVEL_rankscore,REVEL_score,Reliability_index,SIFT4G_converted_rankscore,SIFT4G_pred,SIFT4G_score,SIFT_converted_rankscore,SIFT_pred,SIFT_score,SiPhy_29way_logOdds,SiPhy_29way_logOdds_rankscore,SiPhy_29way_pi,TSL,TWINSUK_AC,TWINSUK_AF,UK10K_AC,UK10K_AF,Uniprot_acc,Uniprot_entry,VEP_canonical,VEST4_rankscore,VEST4_score,VindijiaNeandertal,aaalt,aapos,aaref,alt,bStatistic,bStatistic_converted_rankscore,cds_strand,chr,clinvar_MedGen_id,clinvar_OMIM_id,clinvar_Orphanet_id,clinvar_clnsig,clinvar_hgvs,clinvar_id,clinvar_review,clinvar_trait,clinvar_var_source,codon_degeneracy,codonpos,fathmm-MKL_coding_group,fathmm-MKL_coding_pred,fathmm-MKL_coding_rankscore,fathmm-MKL_coding_score,fathmm-XF_coding_pred,fathmm-XF_coding_rankscore,fathmm-XF_coding_score,genename,gnomAD_exomes_AC,gnomAD_exomes_AF,gnomAD_exomes_AFR_AC,gnomAD_exomes_AFR_AF,gnomAD_exomes_AFR_AN,gnomAD_exomes_AFR_nhomalt,gnomAD_exomes_AMR_AC,gnomAD_exomes_AMR_AF,gnomAD_exomes_AMR_AN,gnomAD_exomes_AMR_nhomalt,gnomAD_exomes_AN,gnomAD_exomes_ASJ_AC,gnomAD_exomes_ASJ_AF,gnomAD_exomes_ASJ_AN,gnomAD_exomes_ASJ_nhomalt,gnomAD_exomes_EAS_AC,gnomAD_exomes_EAS_AF,gnomAD_exomes_EAS_AN,gnomAD_exomes_EAS_nhomalt,gnomAD_exomes_FIN_AC,gnomAD_exomes_FIN_AF,gnomAD_exomes_FIN_AN,gnomAD_exomes_FIN_nhomalt,gnomAD_exomes_NFE_AC,gnomAD_exomes_NFE_AF,gnomAD_exomes_NFE_AN,gnomAD_exomes_NFE_nhomalt,gnomAD_exomes_POPMAX_AC,gnomAD_exomes_POPMAX_AF,gnomAD_exomes_POPMAX_AN,gnomAD_exomes_POPMAX_nhomalt,gnomAD_exomes_SAS_AC,gnomAD_exomes_SAS_AF,gnomAD_exomes_SAS_AN,gnomAD_exomes_SAS_nhomalt,gnomAD_exomes_controls_AC,gnomAD_exomes_controls_AF,gnomAD_exomes_controls_AFR_AC,gnomAD_exomes_controls_AFR_AF,gnomAD_exomes_controls_AFR_AN,gnomAD_exomes_controls_AFR_nhomalt,gnomAD_exomes_controls_AMR_AC,gnomAD_exomes_controls_AMR_AF,gnomAD_exomes_controls_AMR_AN,gnomAD_exomes_controls_AMR_nhomalt,gnomAD_exomes_controls_AN,gnomAD_exomes_controls_ASJ_AC,gnomAD_exomes_controls_ASJ_AF,gnomAD_exomes_controls_ASJ_AN,gnomAD_exomes_controls_ASJ_nhomalt,gnomAD_exomes_controls_EAS_AC,gnomAD_exomes_controls_EAS_AF,gnomAD_exomes_controls_EAS_AN,gnomAD_exomes_controls_EAS_nhomalt,gnomAD_exomes_controls_FIN_AC,gnomAD_exomes_controls_FIN_AF,gnomAD_exomes_controls_FIN_AN,gnomAD_exomes_controls_FIN_nhomalt,gnomAD_exomes_controls_NFE_AC,gnomAD_exomes_controls_NFE_AF,gnomAD_exomes_controls_NFE_AN,gnomAD_exomes_controls_NFE_nhomalt,gnomAD_exomes_controls_POPMAX_AC,gnomAD_exomes_controls_POPMAX_AF,gnomAD_exomes_controls_POPMAX_AN,gnomAD_exomes_controls_POPMAX_nhomalt,gnomAD_exomes_controls_SAS_AC,gnomAD_exomes_controls_SAS_AF,gnomAD_exomes_controls_SAS_AN,gnomAD_exomes_controls_SAS_nhomalt,gnomAD_exomes_controls_nhomalt,gnomAD_exomes_flag,gnomAD_exomes_nhomalt,gnomAD_genomes_AC,gnomAD_genomes_AF,gnomAD_genomes_AFR_AC,gnomAD_genomes_AFR_AF,gnomAD_genomes_AFR_AN,gnomAD_genomes_AFR_nhomalt,gnomAD_genomes_AMI_AC,gnomAD_genomes_AMI_AF,gnomAD_genomes_AMI_AN,gnomAD_genomes_AMI_nhomalt,gnomAD_genomes_AMR_AC,gnomAD_genomes_AMR_AF,gnomAD_genomes_AMR_AN,gnomAD_genomes_AMR_nhomalt,gnomAD_genomes_AN,gnomAD_genomes_ASJ_AC,gnomAD_genomes_ASJ_AF,gnomAD_genomes_ASJ_AN,gnomAD_genomes_ASJ_nhomalt,gnomAD_genomes_EAS_AC,gnomAD_genomes_EAS_AF,gnomAD_genomes_EAS_AN,gnomAD_genomes_EAS_nhomalt,gnomAD_genomes_FIN_AC,gnomAD_genomes_FIN_AF,gnomAD_genomes_FIN_AN,gnomAD_genomes_FIN_nhomalt,gnomAD_genomes_NFE_AC,gnomAD_genomes_NFE_AF,gnomAD_genomes_NFE_AN,gnomAD_genomes_NFE_nhomalt,gnomAD_genomes_POPMAX_AC,gnomAD_genomes_POPMAX_AF,gnomAD_genomes_POPMAX_AN,gnomAD_genomes_POPMAX_nhomalt,gnomAD_genomes_SAS_AC,gnomAD_genomes_SAS_AF,gnomAD_genomes_SAS_AN,gnomAD_genomes_SAS_nhomalt,gnomAD_genomes_flag,gnomAD_genomes_nhomalt,hg18_chr,hg19_chr,integrated_confidence_value,integrated_fitCons_rankscore,integrated_fitCons_score,phastCons100way_vertebrate,phastCons100way_vertebrate_rankscore,phastCons17way_primate,phastCons17way_primate_rankscore,phastCons30way_mammalian,phastCons30way_mammalian_rankscore,phyloP100way_vertebrate,phyloP100way_vertebrate_rankscore,phyloP17way_primate,phyloP17way_primate_rankscore,phyloP30way_mammalian,phyloP30way_mammalian_rankscore,ref,refcodon,rs_dbSNP151 "$BASE.norm.ann.vcf.gz" | $ZIP > "$BASE.norm.ann.dbnsfp.vcf.gz"
    
    echo "# Running SnpSift ClinVar annotation"
    $SNPSIFT annotate "$CLINVAR" -name CLINVAR_ "$BASE.norm.ann.dbnsfp.vcf.gz" | $ZIP > "$BASE.norm.ann.dbnsfp.clinvar.vcf.gz"
    
    echo "# Running SnpSift COSMIC annotation"
    $SNPSIFT annotate "$COSMIC" -name COSMIC_ "$BASE.norm.ann.dbnsfp.clinvar.vcf.gz" | $ZIP > "$BASE.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz"
    
    # Use the fully annotated VCF file as input for vcf2bff
    VCF2BFF_INPUT="$BASE.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz"
else
    # Skip annotation steps and use the original VCF file for conversion
    VCF2BFF_INPUT="$INPUT_VCF"
fi

echo "# Running vcf2bff conversion"
$VCF2BFF -i "$VCF2BFF_INPUT" --project-dir "$PROJECTDIR" --dataset-id "$DATASETID" --genome "$GENOME" -verbose

echo "# Finished OK"
