package main

import (
    "fmt"
    "math/rand"
    "net/http"
)

func predict(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "prediction=%f\n", rand.Float64())
}

func main() {
    http.HandleFunc("/predict", predict)
    fmt.Println("Inference engine listening on :8080")
    http.ListenAndServe(":8080", nil)
}


