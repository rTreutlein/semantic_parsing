;; Function to count alpha-equivalent statements between two spaces
(= (count_alpha_equivalent &space1 &space2)
    (let $count 0
        (match &space1
            ((Statement $head1 $body1) 
                (match &space2
                    ((Statement $head2 $body2)
                        (if (alpha_equivalent? $head1 $body1 $head2 $body2)
                            (+= $count 1) $count)))))))

;; Helper function to check alpha equivalence
(= (alpha_equivalent? $h1 $b1 $h2 $b2)
    (and 
        (eq (normalize_vars $h1) (normalize_vars $h2))
        (eq (normalize_vars $b1) (normalize_vars $b2))))

;; Normalize variables by replacing them with a standard pattern
(= (normalize_vars $expr)
    (match $expr
        ((:$var) (Variable (str "%" (index_of $var (variables_in $expr)))))
        (($head $tail) ( (normalize_vars $head) (normalize_vars $tail) ))
        ($atom $atom)))

;; Extract unique variables from an expression
(= (variables_in $expr)
    (match $expr
        ((:$var) [$var])
        (($head $tail) (concat (variables_in $head) (variables_in $tail)))
        ($atom [])))

;; Test cases
!(assertEqual
    (count_alpha_equivalent 
        [(Statement ":x" "Object") (Statement ":x_is_P" "(P x)")]
        [(Statement ":y" "Object") (Statement ":y_is_P" "(P y)")])
    2)

!(assertEqual
    (count_alpha_equivalent 
        [(Statement ":a" "A") (Statement "(R a b)" "(Q a b)")]
        [(Statement ":c" "A") (Statement "(R c d)" "(Q c d)")])
    2)

!(assertEqual
    (count_alpha_equivalent 
        [(Statement ":x" "Number") (Statement "(> x 0)" "Positive")]
        [(Statement ":y" "String") (Statement "(> y 0)" "Positive")])
    1)
