# QUASAR: search ADaM column names for video-related metadata
CONFIG <- list(
  input_dir = '/domino/datasets/local/clinical-trial-data/CNTO1959UCO3001-QUASAR-LTE-WK188/load-3296/Data/_csv',
  output_dir = '/mnt/data/quasar_video_investigation'
)
if (!dir.exists(CONFIG$input_dir)) stop('Input directory not found: ', CONFIG$input_dir)
dir.create(CONFIG$output_dir, recursive=TRUE, showWarnings=FALSE)
if (file.access(CONFIG$output_dir, 2) != 0) stop('Output directory is not writable')
files <- list.files(CONFIG$input_dir, pattern='\\.csv$', full.names=TRUE, ignore.case=TRUE)
if (!length(files)) stop('No CSV files found')
terms <- c('VIDEO','IMAGE','IMAGING','ENDOS','RECORD','MEDIA','FILE','UPLOAD','CONSENT','CENTRAL','READ','VISIT','SCOPE','STATUS','AVAIL','ASSESS')
pattern <- paste(terms, collapse='|')
results <- list(); errors <- character()
for (f in files) {
  cols <- tryCatch(names(read.csv(f, nrows=0, check.names=FALSE)), error=function(e) {errors <<- c(errors,paste(basename(f),conditionMessage(e))); character()})
  matches <- cols[grepl(pattern,cols,ignore.case=TRUE)]
  if (length(matches)) results[[length(results)+1]] <- data.frame(DATASET=basename(f),VARIABLE=matches,stringsAsFactors=FALSE)
}
output <- if(length(results)) do.call(rbind,results) else data.frame(DATASET=character(),VARIABLE=character())
write.csv(output,file.path(CONFIG$output_dir,'01_adam_column_candidates.csv'),row.names=FALSE,na='')
writeLines(errors,file.path(CONFIG$output_dir,'01_column_scan_errors.txt'))
cat('Files scanned:',length(files),'\nMatching columns:',nrow(output),'\nSaved to:',CONFIG$output_dir,'\n')
print(output,row.names=FALSE)
