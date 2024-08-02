from hyperon import MeTTa
import random
import string

metta = MeTTa()

metta.run('''

(: Nat Type)
(: Z Nat)
(: S (-> Nat Nat))

;; Define <=
(: <= (-> $a $a Bool))
(= (<= $x $y) (or (< $x $y) (== $x $y)))

;; Define cast functions between Nat and Number
(: fromNumber (-> Number Nat))
(= (fromNumber $n) (if (<= $n 0) Z (S (fromNumber (- $n 1)))))
(: fromNat (-> Nat Number))
(= (fromNat Z) 0)
(= (fromNat (S $k)) (+ 1 (fromNat $k)))



(: bc (-> $a                            ; Knowledge base space
          $b                            ; Query
          Nat                           ; Maximum depth
          $b))                          ; Result
;; Base case
(= (bc $kb (: $prf $ccln) $_) (match $kb (: $prf $ccln) (: $prf $ccln)))
;; Recursive step
(= (bc $kb (: ($prfabs $prfarg) $ccln) (S $k))
   (let* (((: $prfabs (-> $prms $ccln)) (bc $kb (: $prfabs (-> $prms $ccln)) $k))
          ((: $prfarg $prms) (bc $kb (: $prfarg $prms) $k)))
     (: ($prfabs $prfarg) $ccln)))

(: fc (-> $a                            ; Knowledge base space
          $b                            ; Source
          Nat                           ; Maximum depth
          $b))                          ; Conclusion
;; Base case
(= (fc $kb (: $prf $prms) $_) (: $prf $prms))
;; Recursive step
(= (fc $kb (: $prfarg $prms) (S $k))
   (let (: $prfabs (-> $prms $ccln)) (bc $kb (: $prfabs (-> $prms $ccln)) $k)
     (fc $kb (: ($prfabs $prfarg) $ccln) $k)))
(= (fc $kb (: $prfabs (-> $prms $ccln)) (S $k))
    (let (: $prfarg $prms) (bc $kb (: $prfarg $prms) $k)
     (fc $kb (: ($prfabs $prfarg) $ccln) $k)))
''')



atoms = ["A","(→ A B)","(→ B C)"]

def generate_random_identifier(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


metta.run('!(bind! &kb (new-space))')


metta.run('''
!(add-atom &kb (: ModusPonens
                (-> (→ $p $q)           ; Premise 1
                    (-> $p              ; Premise 2
                        $q))))          ; Conclusion

''')

for atom in atoms:
    identifier = generate_random_identifier()
    res = metta.run('!(add-atom &kb (: ' + identifier + ' ' + atom + '))')
    print(res)

    res = metta.run('!(fc &kb (: ' + identifier + ' ' + atom + ') (fromNumber 3))')
    print(res)
