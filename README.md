# example6


# Diretório atual dos datasets
data_dir <- getwd()

# Identificar arquivos CSV
files <- list.files(
  data_dir,
  pattern = "\\.csv$",
  full.names = TRUE,
  ignore.case = TRUE
)

# Termos relacionados a vídeos e avaliações
keywords <- paste(
  c(
    "VIDEO", "IMAGE", "IMAGING",
    "ENDOS", "RECORD", "MEDIA",
    "FILE", "UPLOAD", "CONSENT",
    "CENTRAL", "READ", "VISIT"
  ),
  collapse = "|"
)

# Procurar colunas relevantes em todos os ADaM
results <- lapply(files, function(f) {

  cols <- names(
    read.csv(f, nrows = 0, check.names = FALSE)
  )

  matched <- cols[
    grepl(keywords, cols, ignore.case = TRUE)
  ]

  if (length(matched) == 0) return(NULL)

  data.frame(
    DATASET = basename(f),
    VARIABLE = matched
  )
})

results <- Filter(Negate(is.null), results)

if (length(results) > 0) {
  output <- do.call(rbind, results)
  print(output, row.names = FALSE)
  write.csv(
    output,
    "quasar_video_metadata_candidates.csv",
    row.names = FALSE
  )
} else {
  cat("No matching variable names found.\n")
}
