# QUASAR: investigate parameter metadata for video/endoscopy indicators
# Read only metadata-relevant columns; no patient-level exports.
CONFIG <- list(
  input_dir = '/domino/datasets/local/clinical-trial-data/CNTO1959UCO3001-QUASAR-LTE-WK188/load-3296/Data/_csv',
  output_dir = '/mnt/data/quasar_video_investigation',
  datasets = c('admayo.csv','adeff.csv','adeffo.csv'),
  chunk_rows = 25000L
)
if (!dir.exists(CONFIG$input_dir)) stop('Input directory not found: ',CONFIG$input_dir)
dir.create(CONFIG$output_dir,recursive=TRUE,showWarnings=FALSE)
if (file.access(CONFIG$output_dir,2)!=0) stop('Output directory not writable: ',CONFIG$output_dir)
# Includes descriptions, categories, analysis type and source identifiers where present.
metadata_fields <- c('PARAMCD','PARAM','PARCAT1','PARCAT2','PARCAT3','PARCAT4','DTYPE','SRCDOM','SRCVAR','SRCSEQ','AVISIT','AVISITN','VISIT','VISITNUM','ANL01FL','ANL02FL')
keywords <- c('VIDEO','IMAGE','IMAGING','ENDOS','ENDOSCOP','RECORD','MEDIA','FILE','UPLOAD','CONSENT','CENTRAL','READER','READING','AVAILABLE','AVAILABILITY','MISSING','MAYO','SUBSCORE','ASSESS','NOT DONE','NOT PERFORMED')
pattern <- paste(keywords,collapse='|')
# data.table::fread reads only selected columns and can process large CSVs efficiently.
if (!requireNamespace('data.table',quietly=TRUE)) stop('Install data.table in Domino first: install.packages("data.table")')
param_rows <- list(); candidate_rows <- list(); summary_rows <- list()
for (dataset in CONFIG$datasets) {
  path <- file.path(CONFIG$input_dir,dataset)
  if (!file.exists(path)) {warning('Missing: ',path); next}
  cat('Processing ',dataset,'\n',sep='')
  hdr <- tryCatch(names(data.table::fread(path,nrows=0,showProgress=FALSE)),error=function(e) stop(dataset,': ',conditionMessage(e)))
  selected <- intersect(metadata_fields,hdr)
  if (!length(selected)) {warning('No selected metadata columns in ',dataset); next}
  # Load only metadata columns, not patient identifiers, results, or other patient-level data.
  dt <- data.table::fread(path,select=selected,colClasses='character',showProgress=FALSE,na.strings=c('','NA'))
  unique_dt <- unique(dt)
  # Convert all fields to text for robust case-insensitive matching.
  text_matrix <- as.data.frame(unique_dt,stringsAsFactors=FALSE)
  matches <- if(nrow(text_matrix)) apply(text_matrix,1,function(row) any(grepl(pattern,ifelse(is.na(row),'',row),ignore.case=TRUE))) else logical()
  all_df <- as.data.frame(unique_dt,stringsAsFactors=FALSE)
  all_df$DATASET <- dataset
  all_df <- all_df[,c('DATASET',selected),drop=FALSE]
  candidate_df <- all_df[matches,,drop=FALSE]
  param_rows[[dataset]] <- all_df
  candidate_rows[[dataset]] <- candidate_df
  summary_rows[[dataset]] <- data.frame(DATASET=dataset,ROWS_READ=nrow(dt),UNIQUE_METADATA_ROWS=nrow(all_df),MATCHING_METADATA_ROWS=nrow(candidate_df),FIELDS_INSPECTED=paste(selected,collapse='; '),stringsAsFactors=FALSE)
  rm(dt,unique_dt,text_matrix,all_df,candidate_df); gc(verbose=FALSE)
}
combine <- function(x) if(length(x)) data.table::rbindlist(x,fill=TRUE,use.names=TRUE) else data.table::data.table()
all_params <- combine(param_rows)
matched_params <- combine(candidate_rows)
summary <- combine(summary_rows)
data.table::fwrite(all_params,file.path(CONFIG$output_dir,'03_adam_parameter_inventory.csv'),na='')
data.table::fwrite(matched_params,file.path(CONFIG$output_dir,'02_adam_parameter_candidates.csv'),na='')
data.table::fwrite(summary,file.path(CONFIG$output_dir,'04_adam_dataset_summary.csv'),na='')
cat('\nSummary:\n');print(summary)
cat('\nPotential matches (first 30):\n');print(utils::head(matched_params,30))
cat('\nOutput folder: ',CONFIG$output_dir,'\n',sep='')
cat('IMPORTANT: Endoscopy/Mayo scores alone do not prove video file availability.\n')
