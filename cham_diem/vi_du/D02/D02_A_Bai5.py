from sklearn.neighbors import KNeighborsClassifier
X = [[1, 1], [2, 2], [2, 3], [8, 8], [9, 9]]
y = [9, 9, 9, 3, 3]
m = KNeighborsClassifier(n_neighbors=3).fit(X, y)
A = int(m.predict([[3, 3]])[0])
print("A =", A)
