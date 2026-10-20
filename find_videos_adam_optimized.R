# QUASAR-LTE-WK188: memory-conscious ADaM parameter metadata inspection
# Outputs aggregate metadata ONLY; no USUBJID, patient records or clinical values.
CONFIG <- list(
  input_dir = '/domino/datasets/local/clinical-trial-data/CNTO1959UCO3001-QUASAR-LTE-WK188/load-3296/Data/_csv',
  output_dir = '/mnt/data/quasar_video_investigation',
  datasets = c('admayo.csv', 'adeff.csv', 'adeffo.csv'),
  # Keep FALSE: visit-level combinations can greatly inflate unique rows.
  include_visit_columns = FALSE
)

if (!requireNamespace('data.table', quietly = TRUE))
  stop('Package data.table is required. Ask IT or install in your authorized environment.')
if (!dir.exists(CONFIG$input_dir)) stop('Input directory missing: ', CONFIG$input_dir)
dir.create(CONFIG$output_dir, recursive = TRUE, showWarnings = FALSE)
if (file.access(CONFIG$output_dir, 2) != 0)
  stop('Output directory is not writable: ', CONFIG$output_dir)

# Limit to descriptive metadata. Do NOT include SRCSEQ, USUBJID, AVAL, AVALC,
# dates, analysis flags or row-level data in exported results.
metadata_fields <- c('PARAMCD','PARAM','PARCAT1','PARCAT2','PARCAT3','PARCAT4',
                     'DTYPE','SRCDOM','SRCVAR')
if (CONFIG$include_visit_columns)
  metadata_fields <- c(metadata_fields, 'AVISIT','AVISITN','VISIT','VISITNUM')

keywords <- c('VIDEO','IMAGE','IMAGING','ENDOS','ENDOSCOP','RECORD',
              'MEDIA','UPLOAD','CONSENT','CENTRAL','READER','READING',
              'AVAILABLE','AVAILABILITY','MISSING','MAYO','SUBSCORE',
              'ASSESS','NOT DONE','NOT PERFORMED')
pattern <- paste(keywords, collapse = '|')

inventory_file <- file.path(CONFIG$output_dir, '03_adam_parameter_inventory.csv')
candidates_file <- file.path(CONFIG$output_dir, '02_adam_parameter_candidates.csv')
summary_file <- file.path(CONFIG$output_dir, '04_adam_dataset_summary.csv')

# Recreate outputs on every run; each dataset is appended and saved immediately.
for (p in c(inventory_file, candidates_file, summary_file)) if (file.exists(p)) file.remove(p)

# Stable output schema even when different datasets contain different columns.
output_fields <- c('DATASET', metadata_fields)
summary_fields <- c('DATASET','ROWS_READ','UNIQUE_METADATA_ROWS',
                    'MATCHING_METADATA_ROWS','FIELDS_INSPECTED','STATUS')
write_empty <- function(path, fields) {
  x <- as.data.frame(setNames(replicate(length(fields), character(), simplify=FALSE), fields))
  data.table::fwrite(x, path)
}
write_empty(inventory_file, output_fields)
write_empty(candidates_file, output_fields)
write_empty(summary_file, summary_fields)

for (dataset in CONFIG$datasets) {
  cat('\nProcessing ', dataset, ' ...\n', sep=''); flush.console()
  path <- file.path(CONFIG$input_dir, dataset)
  status <- 'OK'; rows_read <- NA_integer_; unique_count <- 0L; match_count <- 0L
  selected <- character()

  tryCatch({
    if (!file.exists(path)) stop('File not found')
    header <- names(data.table::fread(path, nrows=0, showProgress=FALSE))
    selected <- intersect(metadata_fields, header)
    if (!length(selected)) stop('No metadata columns found')
    cat('Reading only: ', paste(selected, collapse=', '), '\n', sep=''); flush.console()

    dt <- data.table::fread(path, select=selected, colClasses='character',
                            na.strings=c('', 'NA'), showProgress=FALSE,
                            nThread=2L)
    rows_read <- nrow(dt)
    # Deduplicate in data.table (avoid apply over a large row matrix).
    dt <- unique(dt, by=selected)
    unique_count <- nrow(dt)
    # Match metadata text only; ignore missing values.
    matched <- rep(FALSE, unique_count)
    for (field in selected) {
      v <- dt[[field]]
      matched <- matched | (!is.na(v) & grepl(pattern, v, ignore.case=TRUE))
    }
    match_count <- sum(matched)

    dt[, DATASET := dataset]
    for (field in setdiff(output_fields, names(dt))) dt[, (field) := NA_character_]
    data.table::setcolorder(dt, output_fields)
    data.table::fwrite(dt, inventory_file, append=TRUE, col.names=FALSE, na='')
    if (match_count) data.table::fwrite(dt[matched], candidates_file,
                                         append=TRUE, col.names=FALSE, na='')
    rm(dt, matched)
    gc(verbose=FALSE)
    cat('Completed: ', rows_read, ' rows read; ', unique_count,
        ' metadata combinations; ', match_count, ' matches.\n', sep='')
  }, error=function(e) {
    status <<- paste('ERROR:', conditionMessage(e))
    cat(status, '\n')
  })

  summary_row <- data.frame(DATASET=dataset, ROWS_READ=rows_read,
                            UNIQUE_METADATA_ROWS=unique_count,
                            MATCHING_METADATA_ROWS=match_count,
                            FIELDS_INSPECTED=paste(selected, collapse='; '),
                            STATUS=status)
  data.table::fwrite(summary_row, summary_file, append=TRUE,
                     col.names=FALSE, na='')
  flush.console()
}
cat('\nDone. Results in: ', CONFIG$output_dir, '\n', sep='')
cat('Endoscopy or Mayo metadata does NOT establish video-file availability.\n')
print(data.table::fread(summary_file, showProgress=FALSE))
